from henry.product.dao import PriceList
from henry.base.serialization import json_dumps

from coreapi import dbapi

with dbapi.session:
    for p in dbapi.search(PriceList):
        print json_dumps(p.serialize())
