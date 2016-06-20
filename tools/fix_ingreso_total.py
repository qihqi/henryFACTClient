import datetime
import json

import requests
from coreapi import dbapi
from henry.base.serialization import json_dumps
from henry.config import transapi
from henry.inventory.dao import Transferencia
from henry.inventory.schema import NTransferencia
from henry.product.dao import ProdItemGroup


def main():
    start = datetime.date(2015, 9, 1)
    end = datetime.date(2016, 6, 12)

    with dbapi.session:
        for x in transapi.search_metadata_by_date_range(start, end):
            raw = requests.get('http://192.168.0.23/app/api/ingreso/{}'.format(x.uid))
            t = Transferencia.deserialize(json.loads(raw.text))
            total = 0
            for i in t.items:
                if i.prod.uid is None:
                    pass
                prod = dbapi.get(i.prod.uid, ProdItemGroup)
                if prod is None:
                    print i.prod.uid
                    continue
                if prod.base_price_usd is None:
                    continue
                total += prod.base_price_usd * i.cant
            t.meta.value = total

            dbapi.db_session.query(NTransferencia).filter_by(id=t.meta.uid).update({'value': total})


if __name__ == '__main__':
    main()
