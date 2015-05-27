import uuid
import datetime
import os
from itertools import imap
from sqlalchemy.exc import SQLAlchemyError

from henry.layer1.schema import NNota, NTransferencia, NPedidoTemporal, NOrdenDespacho
from henry.helpers.serialization import DbMixin, SerializableMixin
from henry.helpers.serialization import json_loads

from .client import Client
from .productos import Product, Transaction


class Status:
    NEW = 'NUEVO'
    COMITTED = 'POSTEADO'
    DELETED = 'ELIMINADO'

    names = (NEW,
             COMITTED,
             DELETED)


class Item(SerializableMixin):
    _name = ('prod', 'cant')

    def __init__(self, prod=None, cant=None):
        self.prod = prod
        self.cant = cant

    @classmethod
    def deserialize(cls, the_dict):
        prod = Product.deserialize(the_dict['prod'])
        cant = the_dict['cant']
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
        'client': 'client',
        'user': 'user',
        'timestamp': 'timestamp',
        'status': 'status',
        'total': 'total',
        'tax': 'tax',
        'subtotal': 'subtotal',
        'discount': 'discount',
        'bodega': 'bodega',
        'almacen': 'almacen'}

    _name = _db_attr.keys()

    def __init__(self,
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
            bodega=None,
            almacen=None):
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
        self.bodega = bodega 
        self.almacen = almacen

    @classmethod
    def deserialize(cls, the_dict):
        x = cls().merge_from(the_dict)
        client = Client.deserialize(the_dict['client'])
        x.client = client
        return x


class Invoice(MetaItemSet):
    _metadata_cls = InvMetadata

    def items_to_transaction(self):
        reason = 'factura: id={} codigo={}'.format(
            self.meta.uid, self.meta.codigo)
        for item in self.items:
            yield Transaction(self.meta.bodega, item.prod.codigo, -item.cant, item.prod.nombre,
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
    REPACKAGE = 'REEMPAQUE'
    EXTERNAL = 'EXTERNA'

    names = (INGRESS,
             TRANSFER,
             REPACKAGE,
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
        pass

    @property
    def filepath_format(self):
        return os.path.join(
            self.meta.timestamp.date().isoformat(), uuid.uuid1().hex)


class DocumentApi:

    def __init__(self, sessionmanager, filemanager, prodapi, object_cls):
        self.db_session = sessionmanager
        self.filemanager = filemanager
        self.prodapi = prodapi

        self.cls = object_cls
        self.metadata_cls = object_cls._metadata_cls
        self.db_class = self.metadata_cls._db_class

    def get_doc(self, uid):
        """
        uid id of the tranfer to fetch,
        returns Transferencia object
        """
        session = self.db_session.session
        db_instance = session.query(self.db_class).filter_by(id=uid).first()
        content = json_loads(self.filemanager.get_file(db_instance.items_location))
        doc = self.cls.deserialize(content)
        #  sometimes db has more updated information
        meta_from_db = self.metadata_cls.from_db_instance(db_instance)
        doc.meta.merge_from(meta_from_db)
        return doc

    def save(self, doc):
        meta = doc.meta
        if not hasattr(meta, 'timestamp'):
            meta.timestamp = datetime.datetime.now()

        doc.validate()
        filepath = doc.filepath_format
        session = self.db_session.session
        db_entry = meta.db_instance()
        db_entry.items_location = filepath
        session.add(db_entry)
        session.flush()  # flush to get the autoincrement id
        meta.status = Status.NEW
        doc.meta.uid = db_entry.id

        self.filemanager.put_file(filepath, doc.to_json())
        return doc

    def commit(self, doc):
        meta = doc.meta
        if meta.status and meta.status != Status.NEW:
            return None
        if self._set_status_and_update_prod_count(
                doc, Status.COMITTED, inverse_transaction=False):
            return doc
        return None

    def delete(self, doc):
        if doc.meta.status != Status.COMITTED:
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
            if inverse_transaction:
                items = imap(lambda i: i.inverse(), items)
            self.prodapi.execute_transactions(items)
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


class PedidoApi:

    def __init__(self, sessionmanager, filemanager):
        self.session = sessionmanager
        self.filemanager = filemanager

    def save(self, raw_content, user=None):
        session = self.session.session
        timestamp = datetime.datetime.now()
        pedido = NPedidoTemporal(
            user=user,
            timestamp=timestamp)
        session.add(pedido)
        session.flush()
        codigo = str(pedido.id)
        filename = os.path.join(timestamp.date().isoformat(), codigo)
        self.filemanager.put_file(filename, raw_content)
        return codigo

    def get(self, uid):
        current_date = datetime.date.today()
        look_back = 7
        uid = str(uid)
        for i in range(look_back):
            cur_date = current_date - datetime.timedelta(days=i)
            filename = os.path.join(cur_date.isoformat(), uid)
            f = self.filemanager.get_file(filename)
            if f is not None:
                return f
        return None


class InvApiOld(object):

    def __init__(self, sessionmanager):
        self.session = sessionmanager

    def get_dated_report(self, start_date, end_date, almacen,
                         seller=None, status=Status.COMITTED):
        dbmeta = self.session.session.query(NOrdenDespacho).filter_by(
            bodega_id=almacen).filter(
            NOrdenDespacho.fecha <= end_date).filter(
            NOrdenDespacho.fecha >= start_date)

        if status == Status.DELETED:
            dbmeta = dbmeta.filter_by(eliminado=True)
        else:
            dbmeta = dbmeta.filter_by(eliminado=False)

        if seller is not None:
            dbmeta = dbmeta.filter_by(vendedor_id=seller)

        return dbmeta