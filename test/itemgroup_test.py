import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from henry.base.dbapi import DBApi
from henry.base.serialization import json_dumps
from henry.base.session_manager import SessionManager

from henry.product.web import create_full_item_from_dict
from henry.product.dao import Inventory, PriceList, ProdItemGroup, ProdItem, Bodega, Store
from henry.schema.base import Base


class ItemApiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        engine = create_engine('sqlite:///:memory:', echo=False)
        sessionfactory = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        cls.sessionmanager = SessionManager(sessionfactory)

        cls.storeapi = DBApi(cls.sessionmanager, Store)
        cls.bodegaapi = DBApi(cls.sessionmanager, Bodega)
        cls.inventoryapi = DBApi(cls.sessionmanager, Inventory)
        cls.priceapi = DBApi(cls.sessionmanager, PriceList)
        cls.itemapi = DBApi(cls.sessionmanager, ProdItem)
        cls.itemgroupapi = DBApi(cls.sessionmanager, ProdItemGroup)

    def test_create_item(self):
        content = {
            "prod": {
                'prod_id': 'ASB',
                'name': 'nombre',
                'desc': '',
                'base_unit': 'unidad',
            },
            "items": [{
                'unit': 'unidad',
                'multiplier': 1,
            }],
            "prices": [
                {
                    'unit': 'unidad',
                    'almacen_id': 1,
                    'display_name': 'nombre display',
                    'price1': 100,
                    'price2': 100,
                    'cant': 0
                },
                {
                    'unit': 'unidad',
                    'almacen_id': 2,
                    'display_name': 'nombre display almacen 2',
                    'price1': 100,
                    'price2': 100,
                    'cant': 0
                },
            ],
            "new_unit": []
        }

        with self.sessionmanager:
            create_full_item_from_dict(
                self.itemgroupapi, self.itemapi, self.priceapi, self.storeapi, self.bodegaapi,
                content)
            self.sessionmanager.commit()
            print json_dumps(self.priceapi.search())


if __name__ == '__main__':
    unittest.main()
