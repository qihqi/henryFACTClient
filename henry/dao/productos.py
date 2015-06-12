import os
import datetime
from itertools import imap

from sqlalchemy.sql import bindparam

from henry.base.schema import (NProducto, NContenido, NStore, NCategory,
                               NBodega, NPriceList)
from henry.base.serialization import SerializableMixin, json_dump
from henry.base.fileservice import LockClass

class Store(SerializableMixin, DbMixin):
    _db_class = NStore
    _db_attr = {
        'almacen_id': 'almacen_id',
        'ruc': 'ruc', 
        'nombre': 'nombre',
        'bodega_id': 'bodega_id'
    }
    _name = _db_attr.keys()


class Bodega(SerializableMixin, DbMixin):
    _db_class = NBodega
    _db_attr = {
        'id': 'almacen_id',
        'nombre': 'nombre',
        'nivel': 'nivel'
    }
    _name = _db_attr.keys()


class Product(SerializableMixin):
    _name = ('nombre',
             'codigo',
             'precio1',
             'precio2',
             'threshold',
             'cantidad',
             'almacen_id',
             'bodega_id')

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


# An augmented product is treated to be a collection of
# products. The representation is '<real_prod_id>+' where
# real_prod_id is a prod_id that exists.
# An augmented product is equivalent to 10x the normal one
# This function returns the real prod id and multiplier(10)
# if it is augmented and None, 0 otherwise
def get_augmented_prod(prod_id):
    if prod_id[-1] == '+':
        return prod_id[:-1], 10
    return None, 0


class Transaction(SerializableMixin):
    _name = ('bodega_id', 'prod_id', 'delta', 'name', 'ref', 'fecha')

    def __init__(self, bodega_id=None,
                 prod_id=None, delta=None,
                 name=None, ref=None, fecha=None):
        self.bodega_id = bodega_id
        self.prod_id = prod_id
        self.delta = delta
        self.name = name
        self.ref = ref
        if fecha is None:
            fecha = datetime.datetime.now()
        self.fecha = fecha

    def inverse(self):
        self.delta = -self.delta
        return self


class TransactionApi:
    def __init__(self, root):
        self.root = root

    def save(self, transaction):
        prod = transaction.prod_id
        fecha = transaction.fecha.date().isoformat()
        dirname = os.path.join(self.root, prod)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        final_path = os.path.join(dirname, fecha)
        with open(final_path, 'a') as f:
            with LockClass(f):
                f.write(json_dump(transaction.serialize()))
                f.write('\n')
                f.flush()

    # generator
    def get_transactions_raw(self, prod_id, date_start, date_end):
        while date_start < date_end:
            fname = os.path.join(self.root, prod_id, date_start)
            with open(fname) as f:
                for line in f.readlines():
                    yield line
            date_start += datetime.timedelta(days=1)

    def get_transactions(self, prod_id, date_start, date_end):
        return imap(Transaction.deserialize,
                    self.get_transactions_raw(prod_id, date_start, date_end))


class ProductApiDB:
    _PROD_KEYS = (
        NProducto.codigo,
        NProducto.nombre,
    )
    _PROD_PRICE_KEYS = (
        NPriceList.nombre,
        NPriceList.prod_id.label('codigo'),
        NPriceList.almacen_id,
        NPriceList.precio1,
        NPriceList.precio2,
        NPriceList.cant_mayorista.label('threshold')
    )
    _PROD_CANT_KEYS = (
        NContenido.cant.label('cantidad'),
        NContenido.bodega_id,
    )

    def __init__(self, sessionmanager, transapi):
        self._prod_name_cache = {}
        self._prod_price_cache = {}
        self._stores = {}
        self._bodegas = {}
        self.db_session = sessionmanager
        self.transapi = transapi

    def get_producto(self, prod_id, almacen_id=None):
        session = self.db_session.session
        query = session.query(*self._PROD_KEYS).filter_by(
            codigo=prod_id)
        if almacen_id:
            query = session.query(*self._PROD_PRICE_KEYS).filter_by(
                prod_id=prod_id).filter_by(almacen_id=almacen_id)
        if query.first() is not None:
            p = Product().merge_from(query.first())
            return p
        return None

    def get_producto_full(self, prod_id):
        items = self.db_session.session.query(
            *(self._PROD_KEYS + self._PROD_PRICE_KEYS +
              (NStore.almacen_id, NStore.nombre.label('almacen_name'), ))).filter(
            NProducto.codigo == prod_id).filter(
            NPriceList.prod_id == prod_id).filter(
            NStore.almacen_id == NPriceList.almacen_id)
        contents = list(items)
        if not contents:
            return None
        p = Product(codigo=contents[0].codigo, nombre=contents[0].nombre)
        p.precios = contents
        return p

    def search_producto(self, prefix, almacen_id=None):
        session = self.db_session.session
        query = session.query(*self._PROD_KEYS).filter(
            NProducto.nombre.startswith(prefix))
        if almacen_id:
            query = session.query(*self._PROD_PRICE_KEYS).filter(
                NPriceList.nombre.startswith(prefix)).filter_by(almacen_id=almacen_id)
        for r in query:
            yield Product().merge_from(r)

    def execute_transactions(self, trans):
        return self.exec_transactions_with_session(self.db_session.session, trans)

    def exec_transactions_with_session(self, session, trans):
        trans = list(trans)
        t = NContenido.__table__.update().where(
            NContenido.prod_id == bindparam('p')).where(
            NContenido.bodega_id == bindparam('b'))
        t = t.values({'cant': NContenido.cant + bindparam('c')})
        substitute = [{'c': x.delta, 'p': x.prod_id, 'b': x.bodega_id}
                      for x in trans]
        result = session.execute(t, substitute)
        for t in trans:
            self.transapi.save(t)
        return result.rowcount

    def get_bodegas(self):
        if not self._bodegas:
            bodegas = self.db_session.session.query(NBodega)
            self._bodegas = {b.id: Bodega.from_db_instance(b) for b in bodegas}
        return self._bodegas.values()

    def get_bodega_by_id(self, uid):
        self.get_bodegas()
        return self._bodegas[uid]

    def get_stores(self):
        if not self._stores:
            stores = self.db_session.session.query(NStore)
            self._stores = {b.almacen_id: Store.from_db_instance(b) for b in stores}
        return self._stores.values()

    def get_store_by_id(self, uid):
        self.get_stores()
        return self._stores[uid]

    def get_category(self):
        return self.db_session.session.query(NCategory)

    def create_product(self, product_core, price_list):
        # insert product in db
        session = self.db_session.session
        prod = NProducto(
            nombre=product_core.nombre,
            codigo=product_core.codigo,
            categoria_id=product_core.categoria)
        session.add(prod)

        # this is a many-to-one relationship
        alm_to_bodega = {x.almacen_id: x.bodega_id for x in self.get_stores()}
        contenidos_creados = {}
        for almacen, (p1, p2, thres) in price_list.items():
            bodega_id = alm_to_bodega[almacen]
            alm = NPriceList(
                prod_id=product_core.codigo,
                almacen_id=almacen,
                precio1=p1,
                precio2=p2,
                cant_mayorista=thres,
                multiplicador=1)
            if bodega_id not in contenidos_creados:
                cont = NContenido(
                    prod_id=product_core.codigo,
                    bodega_id=bodega_id,
                    precio=p1,
                    precio2=p2,
                    cant=0)
                contenidos_creados[bodega_id] = cont
            alm.cantidad = contenidos_creados[bodega_id]
            session.add(alm)
        session.commit()

    def update_prod(self, pid, content_dict):
        session = self.db_session.session
        session.query(NProducto).filter_by(codigo=pid).update(
            content_dict)

    def update_price(self, alm_id, pid, content_dict):
        session = self.db_session.session
        session.query(NPriceList).filter_by(
            prod_id=pid, almacen_id=alm_id).update(
            content_dict)
