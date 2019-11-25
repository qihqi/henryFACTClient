import os
import shutil
import unittest

import datetime

from henry.base.dbapi import DBApiGeneric
from henry.base.fileservice import FileService
from henry.base.session_manager import SessionManager
from henry.sale_records.dao import InvMovementMeta, ItemGroupCant, InvMovementFull, InvMovementManager
from henry.product.dao import ProdItemGroup, InventoryApi
from henry.schema.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class ProductApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        engine = create_engine('sqlite:///:memory:', echo=False)
        sessionfactory = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        cls.sessionmanager = SessionManager(sessionfactory)
        filemanager = FileService('/tmp')
        if os.path.exists('/tmp/1'):
            shutil.rmtree('/tmp/1')
        cls.dbapi = DBApiGeneric(cls.sessionmanager)
        cls.inventoryapi = InventoryApi(filemanager)
        cls.invmomanager = InvMovementManager(cls.dbapi, filemanager, cls.inventoryapi)

    def test_create(self):
        with self.sessionmanager:
            meta = InvMovementMeta()
            meta.timestamp = datetime.datetime(2011, 1, 1, 1, 1)
            meta.inventory_codename = 'boya'
            meta.inventory_docid = 1
            meta.transtype = 'sale'
            meta.origin = 1
            meta.dest = 2
            items = [ItemGroupCant(cant=1, itemgroup=ProdItemGroup(uid=1, prod_id='AAAA'))]
            inv = InvMovementFull(meta=meta, items=items)
            self.invmomanager.create(inv)
            self.assertEquals(1, self.inventoryapi.get_current_quantity(1)[2])


if __name__ == '__main__':
    unittest.main()
