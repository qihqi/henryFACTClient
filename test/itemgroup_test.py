import unittest

from henry.base.dbapi import DBApiGeneric
from henry.base.serialization import json_dumps
from henry.base.session_manager import SessionManager
from henry.product.dao import PriceList, ProdItemGroup, ProdItem, Bodega, Store
from henry.product.web import validate_full_item, create_full_item_from_dict
from henry.schema.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class ItemApiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        engine = create_engine('sqlite:///:memory:', echo=False)
        sessionfactory = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        cls.sessionmanager = SessionManager(sessionfactory)

        cls.dbapi = DBApiGeneric(cls.sessionmanager)

        # make bodega and almacen
        bodegas = [
            Bodega(id=1, nombre='Menorista'),
            Bodega(id=2, nombre='Mayorista'),
            ]
        stores = [
            Store(almacen_id=1, nombre="1", bodega_id=1),
            Store(almacen_id=2, nombre="2", bodega_id=2)]
        with cls.sessionmanager:
            map(cls.dbapi.create, bodegas)
            map(cls.dbapi.create, stores)

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

            "new_unit": []
        }

        with self.sessionmanager:
            result, _ = validate_full_item(content, self.dbapi)
            self.assertTrue(result)
            create_full_item_from_dict(self.dbapi, content)
            self.sessionmanager.session.commit()

            print json_dumps(self.dbapi.search(PriceList))
            self.assertEquals(4, len(self.dbapi.search(PriceList)))
            self.assertEquals(1, len(self.dbapi.search(ProdItemGroup)))
            self.assertEquals(2, len(self.dbapi.search(ProdItem)))

            all_items = self.dbapi.search(ProdItem)
            ids = set(x.itemgroupid for x in all_items)
            self.assertEquals(1, len(ids))

            result, _ = validate_full_item(content, self.dbapi)
            self.assertFalse(result)



if __name__ == '__main__':
    unittest.main()
