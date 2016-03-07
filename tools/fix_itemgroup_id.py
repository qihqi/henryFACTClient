from coreapi import dbapi
from henry.product.dao import ProdItem, ProdItemGroup
from henry.product.dao import get_real_prod_id

__author__ = 'han'

def main():
    with dbapi.session:
        for x in dbapi.search(ProdItem):
            prod_id = get_real_prod_id(x.prod_id)
            itemgroup = dbapi.getone(ProdItemGroup, prod_id=prod_id)
            if itemgroup:
                dbapi.update(x, {'itemgroupid': itemgroup.uid})
            else:
                print prod_id

main()
