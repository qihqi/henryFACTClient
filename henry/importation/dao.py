from henry.base.dbapi import dbmix
from henry.base.serialization import SerializableMixin
from .schema import NUniversalProduct, NDeclaredGood, NPurchaseItem, NPurchase



UniversalProd = dbmix(NUniversalProduct)
Purchase = dbmix(NPurchase)
PurchaseItem = dbmix(NPurchaseItem)
DeclaredGood = dbmix(NDeclaredGood)


class PurchaseFull(SerializableMixin):
    _name = ('meta', 'items')

    def __init__(self, meta=None, items=None):
        self.meta = meta
        self.items = items


class PurchaseItemFull(SerializableMixin):
    _name = ('prod_detail', 'item')

    def __init__(self, prod_detail=None, item=None):
        self.prod_detail = prod_detail
        self.item = item


def get_purchase_full(dbapi, uid):
    purchase = dbapi.get(uid, Purchase)
    items = dbapi.search(PurchaseItem, purchase_id=uid)
    full_items = []
    for i in items:
        fitem = PurchaseItemFull()
        fitem.prod_detail = dbapi.get(i.upi, UniversalProd)
        fitem.item = i
        full_items.append(fitem)
    return PurchaseFull(meta=purchase, items=full_items)


