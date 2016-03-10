from decimal import Decimal
import datetime
from henry.base.dbapi import dbmix
from henry.dao.transaction import Transaction
from henry.product.schema import NInventoryRevision, NInventoryRevisionItem

from .schema import (NBodega, NProducto, NContenido, NCategory, NInventory, NPriceListLabel,
                     NPriceList, NItemGroup, NItem, NStore)

Bodega = dbmix(NBodega)
Product = dbmix(NProducto)
ProdCount = dbmix(NContenido)
Category = dbmix(NCategory)
PriceListLabel = dbmix(NPriceListLabel)
Store = dbmix(NStore)

def convert_decimal(x, default=None):
    return default if x is None else Decimal(x)

price_override_name = (('prod_id', 'codigo'), ('cant_mayorista', 'threshold'))
class PriceList(dbmix(NPriceList, price_override_name)):

    @classmethod
    def deserialize(cls, dict_input):
        prod = super(cls, PriceList).deserialize(dict_input)
        if prod.multiplicador:
            prod.multiplicador = Decimal(prod.multiplicador)
        return prod

class ProdItem(dbmix(NItem)):
    def merge_from(self, the_dict):
        super(ProdItem, self).merge_from(the_dict)
        self.multiplier = convert_decimal(self.multiplier, 1)
        return self


class Inventory(dbmix(NInventory)):
    def merge_from(self, the_dict):
        self = super(Inventory, self).merge_from(the_dict)
        self.quantity = convert_decimal(self.quantity, 0)
        return self

class ProdItemGroup(dbmix(NItemGroup)):
    def merge_from(self, the_dict):
        super(ProdItemGroup, self).merge_from(the_dict)
        self.base_price_usd = convert_decimal(self.base_price_usd, 0)
        return self


def get_real_prod_id(uid):
    if uid[-1] in ('+', '-'):
        return uid[:-1]
    return uid


def make_itemgroup_from_pricelist(pl):
    ig = ProdItemGroup(
        prod_id=get_real_prod_id(pl.prod_id),
        name=get_real_prod_id(pl.nombre))
    if pl.multiplicador == 1:
        ig.base_unit = pl.unidad
        ig.base_unit_usd = pl.precio1
    return ig


def make_item_from_pricelist(pl):
    i = ProdItem(
        prod_id=pl.prod_id,
        multiplier=pl.multiplicador,
        unit=pl.unidad)
    return i


def create_items_chain(dbapi, pl):
    prod_id = get_real_prod_id(pl.prod_id)
    ig = dbapi.getone(ProdItemGroup, prod_id=prod_id)
    if ig is None:
        ig = make_itemgroup_from_pricelist(pl)
        dbapi.create(ig)
    item = dbapi.getone(ProdItem, prod_id=pl.prod_id)
    if item is None:
        item = make_item_from_pricelist(pl)
        item.itemgroupid = ig.uid
        dbapi.create(item)
    pricelist = dbapi.getone(PriceList, prod_id=pl.prod_id, almacen_id=pl.almacen_id)
    if pricelist is None:
        pricelist = PriceList()
        pricelist.merge_from(pl)
        dbapi.create(pricelist)


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
            prod = self.countapi.getone(prod_id=item.prod_id,
                                        bodega_id=revision.bodega_id)
            item.inv_cant = prod.cant
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

