from sqlalchemy.sql import bindparam
from henry.layer1.schema import NProducto, NContenido, NTransferencia, NBodega
from henry.helpers.serialization import SerializableMixin
from henry.layer2.documents import DocumentApi, Status


class TransType:
    INGRESS = 'INGRESO'
    TRANSFER = 'TRANSFER'
    REPACKAGE = 'REEMPAQUE'
    EXTERNAL = 'EXTERNA'

    names = (INGRESS,
             TRANSFER,
             REPACKAGE,
             EXTERNAL)


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
    _name = ('bodega_id', 'prod_id', 'delta', 'name', 'ref')

    def __init__(self, bodega_id=None,
                 prod_id=None, delta=None,
                 name=None, ref=None):
        self.bodega_id = bodega_id
        self.prod_id = prod_id
        self.delta = delta
        self.name = name
        self.ref = ref

    def inverse(self):
        self.delta = -self.delta
        return self


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

    def __init__(self, sessionmanager):
        self._prod_name_cache = {}
        self._prod_price_cache = {}
        self.db_session = sessionmanager

    def get_producto(self, prod_id, almacen_id=None, bodega_id=None):
        query_items = list(ProductApiDB._PROD_KEYS)
        filter_items = [NProducto.codigo == prod_id]
        has_alm = almacen_id is not None
        has_bod = bodega_id is not None
        if has_alm or has_bod:
            filter_items.append(NContenido.prod_id == NProducto.codigo)
        if has_alm:
            query_items.extend(ProductApiDB._PROD_PRICE_KEYS)
            filter_items.append(NContenido.bodega_id == almacen_id)
        if has_bod:
            query_items.extend(ProductApiDB._PROD_CANT_KEYS)
            filter_items.append(NContenido.bodega_id == bodega_id)

        item = self.db_session.session.query(*query_items)
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
        result_proxy = self.db_session.session.query(*query_items)

        for f in filters:
            result_proxy = result_proxy.filter(f)
        for r in result_proxy:
            yield Product().merge_from(r)

    def save(self, prod):
        p = self._construct_db_instance(prod)
        self.db_session.session.add(p)

    def save_batch(self, prods):
        session = self.db_session.session
        for p in prods:
            x = self._construct_db_instance(p)
            session.add(x)

    def execute_transactions(self, trans):
        session = self.db_session.session
        t = NContenido.__table__.update().where(
            NContenido.prod_id == bindparam('p')).where(
            NContenido.bodega_id == bindparam('b'))
        t = t.values({'cant': NContenido.cant + bindparam('c')})
        substitute = [{'c': x.delta, 'p': x.prod_id, 'b': x.bodega_id}
                      for x in trans]
        result = session.execute(t, substitute)
        return result.rowcount

    def exec_transactions_with_session(self, session, trans):
        t = NContenido.__table__.update().where(
            NContenido.prod_id == bindparam('p')).where(
            NContenido.bodega_id == bindparam('b'))
        t = t.values({'cant': NContenido.cant + bindparam('c')})
        substitute = [{'c': x.delta, 'p': x.prod_id, 'b': x.bodega_id}
                      for x in trans]
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
                precio2=prod.precio2)
            p.contenidos.add(c)
        return p

    def get_bodegas(self):
        return self.db_session.session.query(NBodega)


class Metadata(SerializableMixin):
    _name = (
        'uid',
        'origin',
        'dest',
        'user',
        'trans_type',
        'ref',
        'timestamp',
        'status')

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
        self.timestamp = timestamp
        self.status = status


class Transferencia(SerializableMixin):
    _name = ('meta', 'items')

    def __init__(self, meta=None, items=None):
        self.meta = meta
        self.items = items

    @classmethod
    def deserialize(cls, dict_input):
        meta = Metadata.deserialize(dict_input['meta'])
        items = dict_input['items']
        return cls(meta, items)


class TransApiDB(DocumentApi):
    _query_string = (
        NTransferencia.id.label('uid'),
        NTransferencia.status,
        NTransferencia.items_location,
        )
    _db_class = NTransferencia
    _datatype = Transferencia

    def _validate_metadata(self, meta):
        if meta.trans_type is None:
            raise ValueError('Tipo de transferencia no existe')
        if meta.dest is None or meta.dest == -1:
            raise ValueError('ire bodega de destino')
        if (meta.trans_type != TransType.INGRESS and
                meta.origin is None):
            raise ValueError('ire origen para transferencia tipo '
                             + meta.trans_type)

    def create_document_from_request(self, req):
        self._validate_metadata(req.meta)
        t = self._datatype(meta=req.meta)
        t.meta.status = Status.NEW
        new_items = []
        for prod_id, cant in req.items.items():
            p = self.prod_api.get_producto(prod_id)
            if p is None:
                raise ValueError('producto {} no existe'.format(prod_id))
            if cant < 0:
                raise ValueError('Cantidad de producto {} es negativo'
                                 .format(prod_id))
            if cant > 0:
                items = self._item_generator(t.meta, p, cant)
                new_items.extend(items)

        t.items = new_items
        return t

    @classmethod
    def _item_generator(cls, meta, prod, cantidad):
        yield (meta.dest, prod.codigo, cantidad, prod.nombre)
        if meta.trans_type == TransType.TRANSFER:
            yield (meta.origin, prod.codigo, -cantidad, prod.nombre)

    @classmethod
    def _db_instance(cls, meta, filepath):
        db_entry = NTransferencia(
            date=meta.timestamp,
            origin=meta.origin,
            dest=meta.dest,
            trans_type=meta.trans_type,
            status=meta.status,
            items_location=filepath
            )
        return db_entry

    @classmethod
    def _items_to_transactions(cls, transfer):
        reason = 'transfer:' + str(transfer.meta.uid)
        for i in transfer.items:
            bodega_id, prod, cant, name = i
            yield Transaction(bodega_id, prod, cant, name, reason)
