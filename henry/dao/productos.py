import datetime
from decimal import Decimal

from henry.base.dbapi import dbmix
from henry.schema.inventory import NInventoryRevision, NInventoryRevisionItem
from henry.schema.prod import (NBodega, NProducto, NContenido, NCategory,
                               NPriceList, NItemGroup, NItem)
from .coredao import Transaction


Bodega = dbmix(NBodega)
Product = dbmix(NProducto)
ProdCount = dbmix(NContenido)
Category = dbmix(NCategory)
ProdItem = dbmix(NItem)


class ProdItemGroup(dbmix(NItemGroup)):

    @classmethod
    def deserialize(cls, the_dict):
        result = super(cls, ProdItemGroup).deserialize(the_dict)
        if result.base_price_usd:
            result.base_price_usd = Decimal(result.base_price_usd)
        return result


class ProdApi:
    def __init__(self, sessionmanager,
                 store, bodega, prod, count, price, category):
        self.db_session = sessionmanager
        self.store = store
        self.bodega = bodega
        self.prod = prod
        self.count = count
        self.price = price
        self.category = category

    def get_producto_full(self, prod_id):
        all_store = {x.almacen_id: x.nombre for x in self.store.search()}
        all_price = list(self.price.search(prod_id=prod_id))
        prod = self.prod.get(prod_id)
        for p in all_price:
            p.almacen_name = all_store[p.almacen_id]
        prod.precios = all_price
        return prod

    def get_cant_prefix(self, prefix, bodega_id, showall=False):
        session = self.db_session.session
        query = session.query(NContenido, NProducto).filter(
            NContenido.prod_id == NProducto.codigo,
            NProducto.nombre.startswith(prefix),
            NContenido.bodega_id == bodega_id)
        for count, prod in query:
            result = ProdCount.from_db_instance(count)
            result.nombre = prod.nombre
            yield result

    def create_product_full(self, product_core, price_list):
        # insert product in db
        session = self.db_session.session
        prod = NProducto(
            nombre=product_core.nombre,
            codigo=product_core.codigo,
            categoria_id=product_core.categoria)
        session.add(prod)

        # this is a many-to-one relationship
        alm_to_bodega = {x.almacen_id: x.bodega_id for x in
                         self.store.search()}
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


class RevisionApi:
    AJUSTADO = 'AJUSTADO'
    NUEVO = 'NUEVO'
    CONTADO = 'CONTADO'

    def __init__(self, sessionmanager, countapi, transactionapi):
        self.sm = sessionmanager
        self.countapi = countapi
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
        return self.sm.session.query(
            NInventoryRevision).filter_by(uid=rid).first()

    def update_count(self, rid, items_counts):
        revision = self.get(rid)
        if revision is None:
            return None
        for item in revision.items:
            prod = self.countapi.search(prod_id=item.prod_id,
                                        bodega_id=revision.bodega_id)[0]
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
