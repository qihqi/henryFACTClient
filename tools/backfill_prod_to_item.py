from collections import defaultdict
from decimal import Decimal
from coreapi import dbapi
from henry.product.dao import Product, PriceList, ProdItemGroup, ProdItem

def make_item_group(pricelist):
    ig = ProdItemGroup()
    ig.prod_id = pricelist.prod_id
    ig.name = pricelist.nombre
    ig.desc = ''
    ig.baseunit = 'unidad'
    ig.base_price_usd = Decimal(pricelist.precio2) / 100
    return ig

def make_item(pricelist):
    item = ProdItem()
    item.prod_id = pricelist.prod_id
    item.multiplier = pricelist.multiplicador
    item.unit = pricelist.unidad
    return item

def backfill_item(list_of_price):
    if not list_of_price:
        return
    with_plus = None
    without_plus = None

    result = []
    for x in list_of_price:
        if x.prod_id[-1] == '+':
            with_plus = x
        else:
            without_plus = x

    if without_plus is None:
        prod_id = with_plus.prod_id[:-1]
        ig = dbapi.getone(ProdItemGroup, prod_id=prod_id)
        if ig is None:
            print with_plus.serialize()
        return

    ig = dbapi.getone(ProdItemGroup, prod_id=without_plus.prod_id)
    if ig is None:
        ig = make_item_group(without_plus)
        igid = dbapi.create(ig)
        result.append('itemgroup')
    else:
        igid = ig.uid

    item = dbapi.getone(ProdItem, prod_id=without_plus.prod_id)
    if item is None:
        item = make_item(without_plus)
        item.itemgroup_id = igid
        dbapi.create(item)
        result.append('item {}'.format(item.prod_id))
    if with_plus:
        item = dbapi.getone(ProdItem, prod_id=with_plus.prod_id)
        if item is None:
            item = make_item(with_plus)
            item.itemgroup_id = igid
            dbapi.create(item)
            result.append('item {}'.format(item.prod_id))
    return result


def main():
    with dbapi.session as session:
        all_prod = dbapi.search(PriceList)

        by_signature = defaultdict(list)
        for x in all_prod:
            sig = x.prod_id
            if x.prod_id[-1] == '+':
                sig = x.prod_id[:-1]
            by_signature[sig].append(x)

        for x, y in by_signature.items():
            res = backfill_item(y)
            print x, res
        session.commit()

main()