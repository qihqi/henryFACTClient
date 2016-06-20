from coreapi import dbapi
from henry.product.dao import *

def get_prices(dbapi, items):
    prices = []
    for i in items:
        prices.extend(dbapi.search(PriceList, prod_id=i.prod_id))

    return map(lambda x: Decimal(x.precio2 or x.precio1) / x.multiplicador / 100, prices)

def main():

    with dbapi.session:
        to_be_deleted = []
        for ig in dbapi.search(ProdItemGroup, **{'base_price_usd-gte': 31}):
            items = list(dbapi.search(ProdItem, itemgroupid=ig.uid))
            prices = list(get_prices(dbapi, items))
            if not prices:
                print 'delete item', ig.name
                if int(raw_input('delete?')):
                    to_be_deleted.append(ig)
                continue
            price = min(prices)
            print ig.name, price
            print 'updated', dbapi.update(ig, {'base_price_usd': price})
        print 'delete for sure', to_be_deleted
        if int(raw_input('delete')):
            map(dbapi.delete, to_be_deleted)

if __name__ == '__main__':
    main()
        
