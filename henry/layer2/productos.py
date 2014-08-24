import os
import json
import itertools
import uuid
import datetime
from itertools import imap
from collections import namedtuple

from sqlalchemy.sql import bindparam
from henry.layer1.schema import NProducto, NContenido, NTransferencia, NBodega
from henry.helpers.serialization import SerializableMixin, decode

class TransType:
    INGRESS = 'INGRESO'
    TRANSFER= 'TRANSFER'
    REPACKAGE = 'REEMPAQUE'
    EXTERNAL = 'EXTERNA'

    names = (INGRESS,
             TRANSFER,
             REPACKAGE,
             EXTERNAL)


class Status:
    NEW = 'NUEVO'
    COMITTED = 'POSTEADO'
    DELETED = 'ELIMINADO'

    names = (NEW,
             COMITTED,
             DELETED)



class Product(SerializableMixin):
    _name = ('nombre',
             'codigo',
             'precio1',
             'precio2',
             'threshold',
             'cantidad')

    def __init__(self,
                 codigo=None,
                 nombre=None,
                 precio1=None,
                 precio2=None,
                 threshold=None,
                 cantidad=None,
                 almacen_id=None,
                 bodega_id=None):
        self.codigo = codigo
        self.nombre = nombre
        self.almacen_id = almacen_id
        self.precio1 = precio1
        self.precio2 = precio2
        self.threshold = threshold
        self.bodega_id = bodega_id
        self.cantidad = cantidad


class Transaction(SerializableMixin):
    _name=['delta', 'prod_id', 'bodega_id', 'name', 'ref']

    def __init__(self, delta=None, prod_id=None, bodega_id=None, name=None, ref=None):
        self.delta = delta
        self.prod_id = prod_id
        self.bodega_id = bodega_id
        self.name = name
        self.ref = ref


    def inverse(self):
        return Transaction(-self.delta, self.prod_id, self.bodega_id, self.name)

    def serialize(self):
        if self.name is None:
            return (self.delta, self.prod_id, self.bodega_id)
        return self

    @classmethod
    def deserialize(cls, data):
        return cls(*data)


class ProductApiDB:

    _PROD_KEYS = (
        NProducto.codigo,
        NProducto.nombre,
    )
    _PROD_PRICE_KEYS = (
        NContenido.bodega_id.label('almacen_id'),
        NContenido.precio.label('precio1'),
        NContenido.precio2,
        NContenido.cant_mayorista.label('threshold')
    )
    _PROD_CANT_KEYS = (
        NContenido.cant.label('cantidad'),
        NContenido.bodega_id,
    )

    def __init__(self, db_session):
        self._prod_name_cache = {}
        self._prod_price_cache = {}
        self.db_session = db_session

    def get_producto(self, prod_id, almacen_id=None, bodega_id=None):
        query_items = list(ProductApiDB._PROD_KEYS)
        filter_items = [NProducto.codigo == prod_id]
        if almacen_id is not None:
            query_items.extend(ProductApiDB._PROD_PRICE_KEYS)
            filter_items.append(NContenido.prod_id == NProducto.codigo)
            filter_items.append(NContenido.bodega_id == almacen_id)
        if bodega_id is not None:
            query_items.extend(ProductApiDB._PROD_CANT_KEYS)
        item = self.db_session.query(*query_items)
        for f in filter_items:
            item = item.filter(f)
        if item.first() is not None:
            return Product().merge_from(item.first())
        return None

    def search_producto(self, prefix, almacen_id=None, bodega_id=None):
        query_items = list(ProductApiDB._PROD_KEYS)
        filters = [NProducto.nombre.startswith(prefix)]
        if almacen_id is not None:
            query_items.extend(ProductApiDB._PROD_PRICE_KEYS)
            filters.append(NContenido.prod_id == NProducto.codigo)
            filters.append(NContenido.bodega_id == almacen_id)
        if bodega_id is not None:
            query_items.extend(ProductApiDB._PROD_CANT_KEYS)
        result_proxy = self.db_session.query(*query_items)

        for f in filters:
            result_proxy = result_proxy.filter(f)
        for r in result_proxy:
            yield Product().merge_from(r)

    def save(self, prod):
        p = self._construct_db_instance(prod)
        self.db_session.add(p)
        self.db_session.commit()

    def save_batch(self, prods):
        for p in prods:
            x = self._construct_db_instance(p)
            self.db_session.add(x)
        self.db_session.commit()

    def execute_transactions(self, trans):
        rowcount = self.exec_transactions_with_session(self.db_session, trans)
        self.db_session.commit()
        return rowcount

    def exec_transactions_with_session(self, session, trans):
        t = NContenido.__table__.update().where(
                NContenido.prod_id == bindparam('p') and
                NContenido.bodega_id == bindparam('b'))
        t = t.values({'cant': NContenido.cant + bindparam('c')})
        substitute = [{'c': x.delta, 'p': x.prod_id, 'b': x.bodega_id} for x in trans]
        result = session.execute(t, substitute)
        return result.rowcount

    def _construct_db_instance(self, prod):
        p = NProducto(
                codigo=prod.codigo,
                nombre=prod.nombre,
                categoria=prod.categoria)
        if prod.almacen_id:
            c = NContenido(
                    bodega_id=prod.almacen_id,
                    precio=prod.precio1,
                    precio2=prod.precio2,
                    )
            p.contenidos.add(c)
        return p

    def get_bodegas(self):
        return self.db_session.query(NBodega);


class Transferencia(SerializableMixin):
    _name = (
        'uid',
        'origin',
        'dest',
        'user',
        'status',
        'trans_type',
        'items',
        'ref')

    def __init__(self, trans_type=None,
                       uid=None,
                       origin=None,
                       dest=None,
                       user=None,
                       status=None,
                       ref=None,
                       timestamp=None):
        self.uid = uid
        self.origin = origin
        self.dest = dest
        self.user = user
        self.status = status
        self.trans_type = trans_type
        self.ref = ref
        self.timestamp = timestamp or datetime.datetime.now()

        self.status = None
        self.items = []

    def add_item(self, cant, prod_id):
        self.items.append((cant, prod_id))



class TransApiDB:
    _QUERY_KEYS = (
        NTransferencia.id.label('uid'),
        NTransferencia.status,
        NTransferencia.items_location,
        )

    def __init__(self, session, filemanager, prod_api):
        self.db_session = session
        self.filemanager = filemanager
        self.prod_api = prod_api

    def get_doc(self, uid):
        meta = self.db_session.query(*TransApiDB._QUERY_KEYS).filter(
                NTransferencia.id == uid).first()
        if meta is None:
            return None
        parsed = json.loads(self.filemanager.get_file(meta.items_location))
        t = Transferencia.deserialize(parsed)
        t.merge_from(meta)
        return t

    def validate_and_widen(self, transfer):
        if transfer.trans_type is None:
            raise ValueError('Tipo de transferencia no existe')
        if transfer.dest is None:
            raise ValueError('Require bodega de destino')
        if transfer.trans_type != TransType.INGRESS and transfer.origin is None:
            raise ValueError('Require origen para transferencia tipo ' + transfer.trans_type)
        new_items = []
        for row in transfer.items:
            if len(row) < 2:
                raise ValueError('item invalido {}'.format(str(row)))
            cant, prod_id = row[0], row[1]
            p = self.prod_api.get_producto(prod_id)
            if p is None:
                raise ValueError('producto {} no existe'.format(prod_id))
            new_items.append((cant, prod_id, p.nombre))
        transfer.items = new_items
        return transfer

    def save(self, transfer):
        filepath = os.path.join(transfer.timestamp.date().isoformat(), uuid.uuid1().hex)
        transfer = self.validate_and_widen(transfer)
        new_status = transfer.status or Status.NEW
        db_entry = NTransferencia(
            id=transfer.uid,
            date=transfer.timestamp,
            origin=transfer.origin,
            dest=transfer.dest,
            trans_type=transfer.trans_type, status=new_status,
            items_location=filepath
            )
        self.db_session.add(db_entry)
        self.db_session.flush()
        transfer.uid = db_entry.id
        self.filemanager.put_file(filepath, transfer.to_json())
        self.db_session.commit()
        transfer.status = Status.NEW
        return transfer

    def commit(self, transfer):
        if transfer.status and transfer.status != Status.NEW:
            return None

        transfer = self.get_doc(transfer.uid)
        transactions = TransApiDB.items_to_transactions(transfer)
        if not self.prod_api.exec_transactions_with_session(self.db_session, transactions):
            return None
        self.db_session.query(NTransferencia).filter_by(id=transfer.uid).update({'status': Status.COMITTED})
        self.db_session.commit()
        transfer.status = Status.COMITTED
        return transfer

    def delete(self, transfer):
        if transfer.status != Status.COMITTED:
            return None
        transfer = self.get_doc(transfer.uid)
        transactions = TransApiDB.items_to_transactions(transfer)
        inversed = imap(Transaction.inverse, transactions) # revert transactions
        if not self.prod_api.exec_transactions_with_session(self.db_session, inversed):
            return None
        self.db_session.query(NTransferencia).filter_by(id=transfer.uid).update({'status': Status.DELETED})
        self.db_session.commit()
        transfer.status = Status.DELETED
        return transfer

    @classmethod
    def items_to_transactions(cls, transfer):
        reason = 'transfer:' + transfer.uid
        for i in transfer.items:
            cant, prod = i[0], i[1]
            name = i[2] if len(i) > 2 else None
            yield Transaction(cant, prod, transfer.dest, name, reason)
            if transfer.trans_type == TransType.TRANSFER:
                yield Transaction(-cant, prod, tranfer.origin, name, reason)


