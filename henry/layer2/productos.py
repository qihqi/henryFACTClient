import itertools
import datetime
from sqlalchemy.sql import bind_param
from henry.config import new_session
from henry.layer1.schema import NProducto, NContenido, NTransferencia
from henry.helpers.serialization import SerializableMixin, decode


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


class Transaction:
    def __init__(self, prod_id, bodega_id, delta=0):
        self.prod_id = prod_id
        self.bodega_id = bodega_id
        self.delta = delta

    def serialize(self):
        return (self.delta, self.prod_id, self.bodega_id)

    def inverse(self):
        self.delta = -self.delta

class ProductApiDB:

    _PROD_KEYS = [
        NProducto.codigo, 
        NProducto.nombre,
    ]
    _PROD_PRICE_KEYS = [
        NContenido.bodega_id.label('almacen_id'),
        NContenido.precio.label('precio1'),
        NContenido.precio2,
        NContenido.cant_mayorista.label('threshold')
    ]
    _PROD_CANT_KEYS = [
        NContenido.cant,
        NContenido.bodega_id,
    ]

    def __init__(self, db_session):
        self._prod_name_cache = {}
        self._prod_price_cache = {}
        self.db_session = db_session

    def get_producto(self, prod_id, almacen_id=None, bodega_id=None):
        p = Product()
        query_item = ProductApiDB._PROD_KEYS[:]
        filter_items = [NProducto.codigo == prod_id]
        if almacen_id is not None:
            query_item.extend(ProductApiDB._PROD_PRICE_KEYS)
            filter_items.append(NContenido.prod_id == NProducto.codigo)
            filter_items.append(NContenido.bodega_id == almacen_id)
        item = self.db_session.query(*query_item)
        for f in filter_items:
            item = item.filter(f)
        return Product().merge_from(item.first())

    def search_producto(self, prefix, almacen_id=None, bodega_id=None):
        query_items = ProductApiDB._PROD_KEYS[:]
        filters = [NProducto.nombre.startswith(prefix)]
        if almacen_id is not None:
            query_items.extend(ProductApiDB._PROD_PRICE_KEYS)
            filters.append(NContenido.prod_id == NProducto.codigo)
            filters.append(NContenido.bodega_id == almacen_id)
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
        t = NContenido.__table__.update().where(prod_id == bind_param('prod_id'),
                                                bodega_id == bind_param('bodega_id'))
        t = t.values({'cant': NContenido.cant + bind_params('cant'))
        count = self.db_session.execute(t,
            ({'cant': x.delta, 'prod_id': x.prod_id, 'bodega_id': x.bodega_id} for x in trans) 
        self.db_session.commit()
        return count



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

    def __init__(self, **kwargs):
        self.merge_from(kwargs)
        

class TransApiDB:
    _QUERY_KEYS = (
        NTransferencia.id.label('uid'),
        NTransferencia.status,
        NTransferencia.items_location,
        )

    def __init__(self, session, path):
        self.db_session = session
        self.path = path

    def get_doc(self, uid):
        meta = self.db_session.query(*TransApiDB._QUERY_KEYS).filter(
                NTransferencia.id == uid).first()
        t = None
        with open(meta.items_location) as f:
            content = f.read()
            t = Transferencia.deserialize(content)
        t.status = meta.status
        return t

    def save(self, transfer):
        filepath = os.path.join(self.path, transfer.date.isoformat(), transfer.uid)
        as_string = transfer.to_json()
        with open(filepath, 'w') as f:
            f.write(as_string)
        db_entry = NTransferencia(
            id=transfer.uid,
            date=transfer.date,
            origin=transfer.origin,
            dest=transfer.dest,
            trans_type=transfer.trans_type,
            status=Status.NEW,
            items_location=filepath
            )
        self.db_session.add(db_entry)
        self.commit()
        return transfer

    def commit(self, transfer):
        if transfer.status != Status.NEW:
            return None

        if transfer.items is None:
            transfer = self.get_doc(transfer.uid)

        for i in transfer.items:
            cant = i[0]
            prod = i[1]
            bod = i[2]
            update_stmts = get_update_stmt(prod, bod, cant)
            self.db_session.execute(update_stmts)

    




        






