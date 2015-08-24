import datetime
import os
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from henry.base.dbapi import dbmix
from henry.base.serialization import SerializableMixin, json_dumps, json_loads

from henry.schema.prod import NPriceList, NContenido, NStore, NProducto
from henry.schema.user import NCliente, NUsuario


class Client(dbmix(NCliente)):

    @property
    def fullname(self):
        nombres = self.nombres
        if not nombres:
            nombres = ''
        apellidos = self.apellidos
        if not apellidos:
            apellidos = ''
        return apellidos + ' ' + nombres

price_override_name = (('prod_id', 'codigo'), ('cant_mayorista', 'threshold'))


class PriceList(dbmix(NPriceList, price_override_name)):

    @classmethod
    def deserialize(cls, dict_input):
        prod = super(cls, PriceList).deserialize(dict_input)
        if prod.multiplicador:
            prod.multiplicador = Decimal(prod.multiplicador)
        return prod

Store = dbmix(NStore)
User = dbmix(NUsuario)


class Transaction(SerializableMixin):
    _name = ('upi', 'bodega_id', 'prod_id', 'delta',
             'name', 'ref', 'fecha', 'tipo')

    def __init__(self, upi=None, bodega_id=None,
                 prod_id=None, delta=None,
                 name=None, ref=None, fecha=None, tipo=None):
        self.upi = upi
        self.bodega_id = bodega_id
        self.prod_id = prod_id
        self.delta = delta
        self.name = name
        self.ref = ref
        if fecha is None:
            fecha = datetime.datetime.now()
        self.fecha = fecha
        self.tipo = tipo

    def inverse(self):
        self.delta = -self.delta
        return self

    @classmethod
    def deserialize(cls, dict_input):
        result = super(cls, Transaction).deserialize(dict_input)
        result.delta = Decimal(result.delta)
        return result


class TransactionApi:
    def __init__(self, db_session, fileservice):
        self.fileservice = fileservice
        self.db_session = db_session

    def bulk_save(self, transactions):
        for t in transactions:
            self.save(t)

    def save(self, transaction):
        session = self.db_session.session

        upi = getattr(transaction, 'upi', None)
        filter_by = (
                {'bodega_id': transaction.bodega_id,
                 'prod_id': transaction.prod_id}
            if upi is None else {'id': upi})
        cont = session.query(NContenido).filter_by(**filter_by).first()
        if cont is None:  # product does not exist in bodega
            cont = NContenido(
                prod_id=transaction.prod_id,
                bodega_id=transaction.bodega_id,
                precio=0,
                precio2=0,
                cant=transaction.delta)
            try:
                session.add(cont)
                session.flush()
            except IntegrityError:
                session.rollback()
                prod = NProducto(codigo=transaction.prod_id,
                                 nombre=transaction.name)
                prod.contenidos.append(cont)
                session.add(prod)
                session.flush()
        else:
            cont.cant += transaction.delta
            session.flush()
        transaction.upi = cont.id
        transaction.prod_id = cont.prod_id
        transaction.bodega_id = cont.bodega_id
        prod = transaction.prod_id
        fecha = transaction.fecha.date().isoformat()
        data = json_dumps(transaction.serialize())
        self.fileservice.append_file(os.path.join(prod, fecha), data)

    def get_transactions_raw(self, prod_id, date_start, date_end):
        if isinstance(date_start, datetime.datetime):
            date_start = date_start.date()
        if isinstance(date_end, datetime.datetime):
            date_end = date_end.date()

        all_lines = list(self._get_transaction_single(
            prod_id.upper(), date_start, date_end))
        if prod_id.upper() != prod_id.lower():
            all_lines.extend(self._get_transaction_single(
                prod_id.lower(), date_start, date_end))
        return all_lines

    def _get_transaction_single(self, prod_id, date_start, date_end):
        root = os.path.join(self.fileservice.root, prod_id)
        all_names = filter(
            lambda x: date_end.isoformat() >= x >= date_start.isoformat(),
            os.listdir(root)) if os.path.exists(root) else []
        all_names = [os.path.join(prod_id, x) for x in all_names]
        if not all_names:
            return []
        return self.fileservice.get_file_lines(all_names)

    def get_transactions(self, prod_id, date_start, date_end):
        for raw_item in self.get_transactions_raw(
                prod_id, date_start, date_end):
            if raw_item:
                thedict = json_loads(raw_item)
                yield Transaction.deserialize(thedict)
