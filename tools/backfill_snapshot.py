from collections import defaultdict
import datetime
from coreapi import dbapi
from henry.coreconfig import transactionapi
from henry.product.dao import (
    ProdCount, ProdItemGroup, InventoryMovement, InvMovementType)


def main():
    now = datetime.datetime.now()
    now = now - datetime.timedelta(days=1)
    with dbapi.session:
        for x in dbapi.search(ProdCount):
            itemgroup = dbapi.getone(ProdItemGroup, prod_id=x.prod_id)
            if itemgroup:
                t = InventoryMovement(
                    from_inv_id=-1,
                    to_inv_id=x.bodega_id,
                    prod_id=x.prod_id,
                    itemgroup_id=itemgroup.uid,
                    timestamp=now,
                    type=InvMovementType.INITIAL,
                    quantity=x.cant,
                    reference_id=None,
                )
                transactionapi.save(t)
            else:
                print x.bodega_id, x.prod_id, x.cant


if __name__ == '__main__':
    main()
