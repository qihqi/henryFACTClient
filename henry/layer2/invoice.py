import os
from datetime import datetime, date, timedelta
from henry.layer1.schema import NNota, NOrdenDespacho, NPedidoTemporal
from henry.helpers.serialization import SerializableMixin
from henry.layer2.documents import DocumentApi, Status
from henry.layer2.productos import Transaction


class InvMetadata(SerializableMixin):
    _name = (
        'uid',
        'codigo',
        'client',
        'user',
        'timestamp',
        'status',
        'total',
        'tax',
        'subtotal',
        'discount',
        'bodega',
        'almacen')

    def __init__(self, **kwargs):
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = None
        self.__dict__ = kwargs


class Invoice(SerializableMixin):
    _name = ('meta', 'items')

    def __init__(self, meta=None, items=None):
        self.meta = meta
        # list of tuples of (prod_id, cant, name, price)
        self.items = items

    @classmethod
    def deserialize(cls, dict_input):
        meta = InvMetadata.deserialize(dict_input['meta'])
        items = dict_input['items']
        return cls(meta, items)


class InvApiDB(DocumentApi):
    _query_string = (
        NNota.id.label('uid'),
        NNota.status,
        NNota.items_location,
        NNota.codigo,
        )
    _db_class = NNota
    _datatype = Invoice

    def _validate_metadata(self, meta):
        if meta.bodega is None:
            raise ValueError('No tiene bodega')
        if meta.almacen is None:
            raise ValueError('No tiene almacen')

    @classmethod
    def _db_instance(cls, meta, filepath):
        return NNota(
            codigo=meta.codigo,
            client_id=meta.client.codigo,
            user=meta.user,
            timestamp=meta.timestamp,
            status=meta.status,
            total=meta.total,
            tax=meta.tax,
            subtotal=meta.subtotal,
            discount=meta.discount,
            bodega=meta.bodega,
            almacen=meta.almacen,
            items_location=filepath
            )

    @classmethod
    def _items_to_transactions(cls, doc):
        reason = 'factura: id={} codigo={}'.format(
            doc.meta.uid, doc.meta.codigo)
        for i in doc.items:
            prod_id, prod, cant, price = i
            yield Transaction(doc.meta.bodega, prod_id, -cant, prod, ref=reason)

    def create_document_from_request(self, req):
        return req

    def set_codigo(self, uid, codigo):
        self.db_session.session.query(
            NNota).filter_by(id=uid).update({'codigo': codigo})

    def get_doc_by_codigo(self, alm, codigo):
        meta = self.db_session.session.query(
            NNota).filter_by(codigo=codigo, almacen=alm).first()
        return self.get_doc_from_meta(meta)

    def get_dated_report(self, start_date, end_date,
                         almacen, seller=None, status=Status.COMITTED):
        """
        returns an iterable of InvMetadata object that represents sold invoices
        """

        session = self.db_session.session
        dbmeta = session.query(NNota).filter_by(
            almacen=almacen).filter(
            NNota.timestamp < end_date).filter(
            NNota.timestamp >= start_date)
        if seller is not None:
            dbmeta = dbmeta.filter_by(user=seller)

        if status:
            if hasattr(status, '__iter__'):
                exp = NNota.status == status[0]
                for s in status:
                    exp = exp or NNota.status == s
                dbmeta.filter(exp)
            else:
                dbmeta = dbmeta.filter_by(status=status)
        for meta in dbmeta:
            yield InvMetadata().merge_from(meta)


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


class PedidoApi:

    def __init__(self, sessionmanager, filemanager):
        self.session = sessionmanager
        self.filemanager = filemanager

    def save(self, raw_content, user=None):
        session = self.session.session
        timestamp = datetime.now()
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
        current_date = date.today()
        look_back = 7
        uid = str(uid)
        for i in range(look_back):
            cur_date = current_date - timedelta(days=i)
            filename = os.path.join(cur_date.isoformat(), uid)
            f = self.filemanager.get_file(filename)
            if f is not None:
                return f
        return None
