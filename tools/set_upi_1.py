from coreapi import dbapi
from henry.config import transapi
from henry.product.schema import NPriceList


def set_upi_for_ids(dbapi, ids):
    for i in ids:
        x = dbapi.db_session.query(NPriceList).filter(
            NPriceList.almacen_id == 1
        ).filter(NPriceList.prod_id == i or NPriceList.prod_id == i + '+'
        ).update({'upi': 1})
        print i, x

def main():
    transid = 123
    transfer = transapi.get_doc(transid)
    all_ids = [x.prod.prod_id for x in transfer.items]
    with dbapi.session:
        set_upi_for_ids(dbapi, all_ids)
        dbapi.db_session.commit()

if __name__ == '__main__':
    main()

