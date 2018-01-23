from henry.product.dao import PriceList
from henry.base.serialization import json_dumps
from henry.base.dbapi import DBApiGeneric

from henry.coreconfig import sessionmanager
dbapi = DBApiGeneric(sessionmanager)

with dbapi.session:
    for p in dbapi.search(PriceList):
        print json_dumps(p.serialize())
