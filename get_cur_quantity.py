from henry.coreconfig import transactionapi, sessionmanager
from henry.product.schema import NPriceList, NItemGroup, NItem
import sys
import csv


def main():
    with sessionmanager as dbsession:
        res = dbsession.query(NPriceList, NItem, NItemGroup).filter(
                # NPriceList.multiplicador == 1).filter(
                NPriceList.prod_id == NItem.prod_id).filter(
                NItem.itemgroupid == NItemGroup.uid)
        total = 0
        with open(sys.argv[1], 'w') as f:
            writer = csv.writer(f)
            for p, i, ig in res.all():
                cant = sum(x for x in transactionapi.get_current_quantity(ig.uid) if x > 0)
                if cant > 0:
                    writer.writerow([ig.prod_id, ig.desc or p.nombre, ig.base_price_usd, p.precio1, p.precio2, cant])
                    total += (cant * p.precio1 / 100.0)
        print('total is ', total)


main()
