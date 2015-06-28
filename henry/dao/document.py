import logging
import uuid
import datetime
import os
from decimal import Decimal
from itertools import imap

from sqlalchemy.exc import SQLAlchemyError

from henry.base.schema import NNota, NTransferencia, NPedidoTemporal, NOrdenDespacho
from henry.base.serialization import DbMixin, SerializableMixin
from henry.base.serialization import json_loads, parse_iso_date
from .client import Client
from .productos import Product, Transaction


class Status:
    NEW = 'NUEVO'
    COMITTED = 'POSTEADO'
    DELETED = 'ELIMINADO'

    names = (NEW,
             COMITTED,
             DELETED)


class PaymentFormat:
    CASH = "efectivo"
    CARD = "tarjeta"
    CHECK = "cheque"
    DEPOSIT = "deposito"
    CREDIT = "credito"
    VARIOUS = "varios"
    names = (
        CASH,
        CARD,
        CHECK,
        DEPOSIT,
        CREDIT,
        VARIOUS,
    )


class Item(SerializableMixin):
    _name = ('prod', 'cant')

    def __init__(self, prod=None, cant=None):
        self.prod = prod
        self.cant = cant

    @classmethod
    def deserialize(cls, the_dict):
        prod = Product.deserialize(the_dict['prod'])
        cant = Decimal(the_dict['cant'])
        return cls(prod, cant)


class MetaItemSet(SerializableMixin):
    _name = ('meta', 'items')

    def __init__(self, meta=None, items=None):
        self.meta = meta
        self.items = list(items) if items else []

    def items_to_transaction(self):
        raise NotImplementedError()

    @classmethod
    def deserialize(cls, the_dict):
        x = cls()
        x.meta = cls._metadata_cls.deserialize(the_dict['meta'])
        x.items = map(Item.deserialize, the_dict['items'])
        return x


class InvMetadata(SerializableMixin, DbMixin):
    _db_class = NNota
    _excluded_vars = ('client',)
    _db_attr = {
        'uid': 'id',
        'codigo': 'codigo',
        'user': 'user_id',
        'timestamp': 'timestamp',
        'status': 'status',
        'total': 'total',
        'tax': 'tax',
        'tax_percent': 'tax_percent',
        'discount_percent': 'discount_percent',
        'subtotal': 'subtotal',
        'discount': 'discount',
        'bodega_id': 'bodega_id',
        'paid': 'paid',
        'paid_amount': 'paid_amount',
        'almacen_id': 'almacen_id',
        'payment_format': 'payment_format'}

    _name = tuple(_db_attr.keys()) + ('client',)

    def __init__(
            self,
            uid=None,
            codigo=None,
            client=None,
            user=None,
            timestamp=None,
            status=None,
            total=None,
            tax=None,
            subtotal=None,
            discount=None,
            bodega_id=None,
            tax_percent=None,
            discount_percent=None,
            paid=None,
            paid_amount=None,
            payment_format=None,
            almacen_id=None):
        self.uid = uid
        self.codigo = codigo
        self.client = client
        self.user = user
        self.timestamp = timestamp if timestamp else datetime.datetime.now()
        self.status = status
        self.total = total
        self.tax = tax
        self.subtotal = subtotal
        self.discount = discount
        self.bodega_id = bodega_id
        self.almacen_id = almacen_id
        self.tax_percent = tax_percent
        self.discount_percent = discount_percent
        self.paid = paid
        self.payment_format = payment_format
        self.paid_amount = paid_amount

    @classmethod
    def deserialize(cls, the_dict):
        x = cls().merge_from(the_dict)
        if not isinstance(x.timestamp, datetime.datetime):
            x.timestamp = parse_iso_date(x.timestamp)
        if 'client' in the_dict:
            client = Client.deserialize(the_dict['client'])
            x.client = client
        else:
            x.client = None
        return x

    def db_instance(self):
        db_instance = super(InvMetadata, self).db_instance()
        db_instance.client_id = self.client.codigo
        return db_instance

    @classmethod
    def from_db_instance(cls, db_instance):
        this = super(InvMetadata, cls).from_db_instance(db_instance)
        this.client = Client()
        this.client.codigo = db_instance.client_id
        return this


class Invoice(MetaItemSet):
    _metadata_cls = InvMetadata

    def items_to_transaction(self):
        reason = 'factura: id={} codigo={}'.format(
            self.meta.uid, self.meta.codigo)
        for item in self.items:
            pid = item.prod.codigo
            cant = item.cant
            if pid[-1] == '+' or pid[-1] == '-':
                cant = cant * (Decimal(10) if pid[-1] == '+' else Decimal('0.5'))
                pid = pid[:-1]
            yield Transaction(self.meta.bodega_id, pid, -cant, item.prod.nombre,
                              reason, self.meta.timestamp)

    def validate(self):
        if getattr(self.meta, 'codigo', None) is None:
            raise ValueError('codigo cannot be None to save an invoice')

    @property
    def filepath_format(self):
        return os.path.join(
            self.meta.timestamp.date().isoformat(), self.meta.codigo)


class TransType:
    INGRESS = 'INGRESO'
    TRANSFER = 'TRANSFER'
    EXTERNAL = 'EXTERNA'

    names = (INGRESS,
             TRANSFER,
             EXTERNAL)


class TransMetadata(SerializableMixin, DbMixin):
    _db_attr = {
        'uid': 'id',
        'origin': 'origin',
        'dest': 'dest',
        'user': 'user',
        'trans_type': 'trans_type',
        'ref': 'ref',
        'timestamp': 'timestamp',
        'status': 'status'}
    _name = _db_attr.keys()
    _db_class = NTransferencia

    def __init__(self,
                 trans_type=None,
                 uid=None,
                 origin=None,
                 dest=None,
                 user=None,
                 ref=None,
                 status=None,
                 timestamp=None):
        self.uid = uid
        self.origin = origin
        self.dest = dest
        self.user = user
        self.trans_type = trans_type
        self.ref = ref
        self.timestamp = timestamp if timestamp else datetime.datetime.now()
        self.status = status

    @classmethod
    def deserialize(cls, the_dict):
        x = super(cls, TransMetadata).deserialize(the_dict)
        if not isinstance(x.timestamp, datetime.datetime):
            x.timestamp = parse_iso_date(x.timestamp)
        return x


class Transferencia(MetaItemSet):
    _metadata_cls = TransMetadata

    def items_to_transaction(self):
        reason = 'ingreso: codigo={}'
        if self.meta.trans_type == TransType.TRANSFER:
            reason = 'transferencia: codigo = {}'
        reason = reason.format(self.meta.uid)
        for item in self.items:
            prod, cant = item.prod, item.cant
            if self.meta.origin:
                yield Transaction(self.meta.origin, prod.codigo, -cant, prod.nombre,
                                  reason, self.meta.timestamp)
            if self.meta.dest:
                yield Transaction(self.meta.dest, prod.codigo, cant, prod.nombre,
                                  reason, self.meta.timestamp)

    def validate(self):
        if self.meta.trans_type != TransType.EXTERNAL:
            if self.meta.dest is None:
                raise ValueError('dest is none for non external')
        else:
            self.meta.dest = None
        if self.meta.trans_type != TransType.INGRESS:
            if self.meta.origin is None:
                raise ValueError('origin is none for non ingress')
        else:
            self.meta.origin = None

    @property
    def filepath_format(self):
        path = getattr(self, '_path', None)
        if path is None:
            self._path = os.path.join(
                self.meta.timestamp.date().isoformat(), uuid.uuid1().hex)
        return self._path


class DocumentApi:
    def __init__(self, sessionmanager, filemanager, transaction, object_cls):
        self.db_session = sessionmanager
        self.filemanager = filemanager
        self.transaction = transaction

        self.cls = object_cls
        self.metadata_cls = object_cls._metadata_cls
        self.db_class = self.metadata_cls._db_class

    def get_doc(self, uid):
        session = self.db_session.session
        db_instance = session.query(self.db_class).filter_by(id=uid).first()
        if db_instance is None:
            print 'cannot find document in table ', self.db_class.__tablename__,
            print ' with id ', uid
            return None
        doc = self.get_doc_from_file(db_instance.items_location)
        doc.meta.status = db_instance.status
        return doc

    def get_doc_from_file(self, filename):
        file_content = self.filemanager.get_file(filename)
        if file_content is None:
            print 'could not find file at ', filename
            return None
        content = json_loads(file_content)
        doc = self.cls.deserialize(content)
        return doc

    def save(self, doc):
        meta = doc.meta
        if not hasattr(meta, 'timestamp'):
            meta.timestamp = datetime.datetime.now()
        if not meta.status:
            meta.status = Status.NEW
        doc.validate()
        filepath = doc.filepath_format
        session = self.db_session.session
        db_entry = meta.db_instance()
        db_entry.items_location = filepath
        session.add(db_entry)
        session.flush()  # flush to get the autoincrement id
        doc.meta.uid = db_entry.id

        self.filemanager.put_file(filepath, doc.to_json())
        return doc

    def commit(self, doc):
        meta = doc.meta
        if meta.status and meta.status != Status.NEW:
            logging.info('attempt to commit doc {} in wrong status'.format(doc.meta.uid))
            return None
        if self._set_status_and_update_prod_count(
                doc, Status.COMITTED, inverse_transaction=False):
            return doc
        return None

    def delete(self, doc):
        if doc.meta.status != Status.COMITTED:
            logging.info('attempt to delete doc {} which is not committed'.format(doc.meta.uid))
            return None
        if self._set_status_and_update_prod_count(
                doc, Status.DELETED, inverse_transaction=True):
            return doc
        return None

    def _set_status_and_update_prod_count(
            self, doc, new_status, inverse_transaction):
        session = self.db_session.session
        try:
            items = list(doc.items_to_transaction())
            for i in items:
                i.ref = '{}: {}'.format(new_status, i.ref)
                if inverse_transaction:
                    i.inverse()
            self.transaction.bulk_save(items)
            session.query(self.db_class).filter_by(
                id=doc.meta.uid).update({'status': new_status})
            session.commit()
            doc.meta.status = new_status
            return True
        except SQLAlchemyError:
            import traceback

            traceback.print_exc()
            session.rollback()
            return False

    def search_metadata_by_date_range(self, start, end, status=None, other_filters=None):
        session = self.db_session.session
        query = session.query(self.db_class).filter(
            self.db_class.timestamp >= start).filter(
            self.db_class.timestamp <= end)
        if status is not None:
            query = query.filter_by(status=status)
        if other_filters is not None:
            query = query.filter_by(**other_filters)
        for r in query:
            meta = self.metadata_cls.from_db_instance(r)
            meta.items_location = r.items_location
            yield meta


class PedidoApi:
    def __init__(self, sessionmanager, filemanager):
        self.session = sessionmanager
        self.filemanager = filemanager

    def save(self, raw_content, user=None, status='pedido'):
        session = self.session.session
        timestamp = datetime.datetime.now()
        pedido = NPedidoTemporal(
            user=user,
            timestamp=timestamp,
            status=status)
        session.add(pedido)
        session.flush()
        codigo = str(pedido.id)
        filename = os.path.join(timestamp.date().isoformat(), codigo)
        filename = self.filemanager.put_file(filename, raw_content)
        return codigo, filename

    def get_doc(self, uid):
        current_date = datetime.date.today()
        look_back = 7
        uid = str(uid)
        for i in range(look_back):
            cur_date = current_date - datetime.timedelta(days=i)
            filename = os.path.join(cur_date.isoformat(), uid)
            f = self.filemanager.get_file(filename)
            if f is not None:
                return f
        logging.info('Could not find pedido within {} days of lookback'.format(look_back))
        return None


class InvApiOld(object):
    def __init__(self, sessionmanager):
        self.session = sessionmanager

    def get_dated_report(self, start_date, end_date, almacen,
                         seller=None, status=Status.COMITTED):
        dbmeta = self.session.session.query(NOrdenDespacho).filter_by(
            bodega_id=almacen).filter(
            NOrdenDespacho.fecha < end_date).filter(
            NOrdenDespacho.fecha >= start_date)

        if status == Status.DELETED:
            dbmeta = dbmeta.filter_by(eliminado=True)
        else:
            dbmeta = dbmeta.filter_by(eliminado=False)

        if seller is not None:
            dbmeta = dbmeta.filter_by(vendedor_id=seller)

        return dbmeta
