from decimal import Decimal
from ..base.dbapi import dbmix

from .schema import (NBodega, NProducto, NContenido, NCategory, NInventory, NPriceListLabel,
                     NPriceList, NItemGroup, NItem, NStore)

Bodega = dbmix(NBodega)
Product = dbmix(NProducto)
ProdCount = dbmix(NContenido)
Category = dbmix(NCategory)
PriceListLabel = dbmix(NPriceListLabel)
Store = dbmix(NStore)
PriceList = dbmix(NPriceList)

def convert_decimal(x, default=None):
    return default if x is None else Decimal(x)


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
