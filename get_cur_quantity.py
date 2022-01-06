from decimal import Decimal
from collections import defaultdict
from henry.coreconfig import transactionapi, sessionmanager
from henry.product.schema import NPriceList, NItemGroup, NItem
import sys
import csv

def tally_ig(ig):
    return 0


class ItemGroup:

    def __init__(self):
        self.uid = 0
        self.name = ''
        self.price = 1 << 32
        self.unit = 'UNIDAD'
        self.mult = 0
        self.min_unit = 'UNIDAD'
    # price
    # unit
    # mult
    # id
    # name

def minprice(p1, p2):
    if p2 is None or p2 == 0:
        return p1
    if p1 is None or p1 == 0:
        return p2
    return min(p1, p2)


def main():
    igs = defaultdict(ItemGroup)

    with sessionmanager as dbsession:
        res = dbsession.query(NPriceList, NItem, NItemGroup).filter(
                # NPriceList.multiplicador == 1).filter(
                NPriceList.prod_id == NItem.prod_id).filter(
                NItem.itemgroupid == NItemGroup.uid)
        for p, i, ig in res.all():
            newig = igs[ig.uid]
            newig.name = ig.name
            newig.uid = ig.uid
            newig.prod_id = ig.prod_id
            minp = Decimal(minprice(p.precio1, p.precio2)) / 100 / i.multiplier
            
            if minp > 0 and newig.price > minp:
                newig.price = minp

            if newig.mult < i.multiplier:
                newig.mult = i.multiplier
                newig.unit = i.unit
            if i.multiplier == 1:
                newig.min_unit = i.unit

        total = 0
        with open(sys.argv[1], 'w') as f:
            writer = csv.writer(f)
            for ig in igs.values():
                writer.writerow([ig.uid, ig.prod_id, ig.name, ig.price, ig.mult, ig.unit, ig.min_unit])
        print('total is ', total)


main()
