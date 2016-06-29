import datetime
from henry.product.dao import ProdItemGroup, InventoryMovement, InventoryApi
from henry.base.serialization import json_dumps
from henry.base.dbapi import DBApiGeneric
from henry.base.fileservice import FileService

from henry.constants import TRANSACTION_PATH
from henry.coreconfig import sessionmanager


START = datetime.date(2016, 3, 1)
END = datetime.date(2016, 6, 22)


def main():
    dbapi = DBApiGeneric(sessionmanager)
    transactionapi = InventoryApi(FileService(TRANSACTION_PATH))
    with dbapi.session:
        for ig in dbapi.search(ProdItemGroup):
            trans = transactionapi.list_transactions(ig.uid, 
                START, END)
            print json_dumps([ig, list(trans)])

if __name__ == '__main__':
    main()


        
