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

        # make bodega and almacen
        bodegas = [
            Bodega(id=1, nombre='Menorista'),
            Bodega(id=2, nombre='Mayorista'),
            ]
        stores = [
            Store(almacen_id=1, nombre="1", bodega_id=1),
            Store(almacen_id=2, nombre="2", bodega_id=2)]
        with cls.sessionmanager:
            map(cls.bodegaapi.create, bodegas)
            map(cls.storeapi.create, stores)


    def test_create_item(self):
        content = {
            "prod": {
                'prod_id': 'ASB',
                'name': 'nombre',
                'desc': '',
                'base_unit': 'unidad',
            },
            "items": [
                {
                    'unit': 'unidad',
                    'multiplier': 1,
                    'prices': {
                        "1": {
                            'display_name': 'nombre display',
                            'price1': 100,
                            'price2': 100,
                            'cant': 0
                        },
                        "2": {
                            'display_name': 'nombre display',
                            'price1': 100,
                            'price2': 100,
                            'cant': 0
                        }
                    },
                },
                {
                    'unit': 'paquete',
                    'multiplier': 100,
                    'prices': {
                        "1": {
                            'display_name': 'nombre display',
                            'price1': 100,
                            'price2': 100,
                            'cant': 0
                        },
                        "2": {
                            'display_name': 'nombre display',
                            'price1': 100,
                            'price2': 100,
                            'cant': 0
                        }
                    }
                },

            ],

            "prices": [
                {
                    'unit': 'paquete',
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
                self.inventoryapi,
                content)
            self.sessionmanager.session.commit()

            print json_dumps(self.priceapi.search())
            self.assertEquals(4, len(self.priceapi.search()))
            self.assertEquals(1, len(self.itemgroupapi.search()))
            self.assertEquals(2, len(self.itemapi.search()))
            self.assertEquals(4, len(self.inventoryapi.search()))

            self.assertEquals(1, len(self.priceapi.search(upi=1)))

            all_items = self.itemapi.search()
            ids = set(x.itemgroupid for x in all_items)
            self.assertEquals(1, len(ids))



if __name__ == '__main__':
    unittest.main()
