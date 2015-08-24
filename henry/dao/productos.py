import os
import datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from henry.schema.inventory import NInventoryRevision, NInventoryRevisionItem, NCategory, NBodega, NProducto, NContenido
from henry.schema.core import NPriceList, NStore
from henry.base.serialization import SerializableMixin, json_dumps, DbMixin, json_loads
from henry.base.dbapi import dbmix


Store = dbmix(NStore)
Bodega = dbmix(NBodega)


class AllProdApi:

    def __init__(self, bodapi, alm, itemgroup, item, pricelist):
        self.bod = bodapi
        self.alm = alm
        self.itemgroup = itemgroup
        self.item = item
        self.pricelist = pricelist


class Product(SerializableMixin):
    _name = ('nombre',
             'codigo',
             'precio1',
             'precio2',
             'threshold',
             'cantidad',
             'almacen_id',
             'bodega_id',
             'upi',
             'multiplicador',
             'inactivo',)

    def __init__(self,
                 codigo=None,
                 nombre=None,
                 precio1=None,
                 precio2=None,
                 threshold=None,
                 cantidad=None,
                 almacen_id=None,
                 bodega_id=None,
                 upi=None,
                 multiplicador=None,
                 inactivo=None):
        self.codigo = codigo
        self.nombre = nombre
        self.almacen_id = almacen_id
        self.precio1 = precio1
        self.precio2 = precio2
        self.threshold = threshold
        self.bodega_id = bodega_id
        self.cantidad = cantidad
        self.upi = upi
        self.multiplicador = multiplicador
        self.inactivo = inactivo

    @classmethod
    def deserialize(cls, dict_input):
        prod = super(cls, Product).deserialize(dict_input)
        if prod.multiplicador:
            prod.multiplicador = Decimal(prod.multiplicador)
        return prod




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
        NPriceList.cant_mayorista.label('threshold'),
        NPriceList.upi,
        NPriceList.multiplicador
    )
    _PROD_CANT_KEYS = (
        NContenido.cant.label('cantidad'),
        NContenido.bodega_id,
        NContenido.inactivo,
    )

    def __init__(self, sessionmanager):
        self.db_session = sessionmanager

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

    def get_cant(self, prod_id, bodega_id):
        session = self.db_session.session
        item = session.query(*(self._PROD_KEYS + self._PROD_CANT_KEYS)).filter(
            NProducto.codigo == prod_id, NContenido.prod_id == prod_id,
            NContenido.bodega_id == bodega_id, NContenido.inactivo != True).first()
        if item is not None:
            return Product().merge_from(item)
        return None

    def get_cant_prefix(self, prefix, bodega_id, showall=False):
        session = self.db_session.session
        query = session.query(*(self._PROD_KEYS + self._PROD_CANT_KEYS)).filter(
            NProducto.nombre.startswith(prefix), NContenido.prod_id == NProducto.codigo,
            NContenido.bodega_id == bodega_id)
        if not showall:
            query = query.filter(NContenido.inactivo != True)
        for r in query:
            yield Product().merge_from(r)

    def get_producto_full(self, prod_id):

        items = self.db_session.session.query(
            *(self._PROD_PRICE_KEYS +
              (NStore.almacen_id, NStore.nombre.label('almacen_name'), ))).filter(
            NPriceList.prod_id == prod_id).filter(
            NStore.almacen_id == NPriceList.almacen_id)

        contents = list(items)
        p = self.get_producto(prod_id)
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

    def get_bodegas(self):
        bodegas = self.db_session.session.query(NBodega)
        return {b.id: Bodega.from_db_instance(b) for b in bodegas}

    def get_bodega_by_id(self, uid):
        bodegas = self.get_bodegas()
        return bodegas[uid]

    def get_stores(self):
        stores = self.db_session.session.query(NStore)
        return {b.almacen_id: Store.from_db_instance(b) for b in stores}

    def get_store_by_id(self, uid):
        stores = self.get_stores()
        return stores[uid]

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
                nombre=product_core.nombre,
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

    def update_or_create_price(self, alm_id, pid, content_dict):
        session = self.db_session.session
        count = session.query(NPriceList).filter_by(
            prod_id=pid, almacen_id=alm_id).update(
            content_dict)
        if count == 0:  # did not match any row
            store = self.get_store_by_id(alm_id)
            prod, cont = session.query(NProducto, NContenido).filter(
                NProducto.codigo == NContenido.prod_id).filter(
                NProducto.codigo == pid, NContenido.bodega_id == store.bodega_id).first()
            content_dict.update({
                'almacen_id': alm_id,
                'prod_id': pid,
                'nombre': prod.nombre,
                'upi': cont.id,
                'multiplicador': 1,
                'unidad': 'unidad',
            })
            newprice = NPriceList(**content_dict)
            session.add(newprice)


class RevisionApi:
    AJUSTADO = 'AJUSTADO'
    NUEVO = 'NUEVO'
    CONTADO = 'CONTADO'

    def __init__(self, sessionmanager, prodapi, transactionapi):
        self.sm = sessionmanager
        self.prodapi = prodapi
        self.transactionapi = transactionapi

    def save(self, bodega_id, user_id, items):
        session = self.sm.session
        revision = NInventoryRevision()
        revision.bodega_id = bodega_id
        revision.timestamp = datetime.datetime.now()
        revision.created_by = user_id
        revision.status = self.NUEVO
        for prod_id in items:
            item = NInventoryRevisionItem(prod_id=prod_id)
            revision.items.append(item)
        session.add(revision)
        session.flush()
        return revision

    def get(self, rid):
        return self.sm.session.query(NInventoryRevision).filter_by(uid=rid).first()

    def update_count(self, rid, items_counts):
        revision = self.get(rid)
        if revision is None:
            return None
        for item in revision.items:
            prod = self.prodapi.get_cant(item.prod_id, revision.bodega_id)
            item.inv_cant = prod.cantidad
            item.real_cant = items_counts[item.prod_id]

        revision.status = self.CONTADO
        self.sm.session.flush()
        return revision

    def commit(self, rid):
        revision = self.get(rid)
        if revision is None:
            return None
        if revision.status != 'CONTADO':
            return revision
        reason = 'Revision: codigo {}'.format(rid)
        now = datetime.datetime.now()
        bodega_id = revision.bodega_id
        for item in revision.items:
            delta = item.real_cant - item.inv_cant
            transaction = Transaction(
                upi=None,
                bodega_id=bodega_id,
                prod_id=item.prod_id,
                delta=delta,
                ref=reason,
                fecha=now)
            self.transactionapi.save(transaction)
        revision.status = 'AJUSTADO'
        return revision
