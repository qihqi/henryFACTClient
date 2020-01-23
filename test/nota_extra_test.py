from __future__ import print_function
from builtins import map
import unittest
import datetime

from henry.base.dbapi import DBApiGeneric
from henry.base.fileservice import FileService 
from henry.base.serialization import json_dumps
from henry.base.session_manager import SessionManager
from henry.dao.document import Item, DocumentApi
from henry.invoice.coreapi import make_nota_api
from henry.invoice.api import make_nota_all
from henry.invoice.dao import Invoice, InvMetadata, NotaExtra, SRINota
from henry.product.web import validate_full_item, create_full_item_from_dict
from henry.product.dao import PriceList, ProdItemGroup, ProdItem, Bodega, Store
from henry.product.dao import InventoryApi
from henry.users.dao import Client
from henry.schema.base import Base
from tools import send_to_cloud
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from webtest import TestApp


class ItemApiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        engine = create_engine('sqlite:///:memory:', echo=False)
        sessionfactory = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        cls.sessionmanager = SessionManager(sessionfactory)

        cls.dbapi = DBApiGeneric(cls.sessionmanager)
        transactionapi = InventoryApi(FileService('/tmp/1'))
        cls.invapi = DocumentApi(cls.sessionmanager, FileService('/tmp/2'),
                                 transactionapi, object_cls=Invoice)
        actionlogged = lambda x:x
        auth_decorator = lambda x: (lambda y: y)
        pedidoapi = None # will not be used in this test
        workerqueue = None
        wsgi = make_nota_api(
            '/api',
            dbapi=cls.dbapi, actionlogged=actionlogged, 
            invapi=cls.invapi, auth_decorator=auth_decorator,
            pedidoapi=pedidoapi, workerqueue=workerqueue)

        cls.test_app = TestApp(wsgi)
        wsgi_remote = make_nota_all('/api2', cls.dbapi, actionlogged, 
                                    FileService('/tmp/3'), auth_decorator)
        cls.test_app_remote = TestApp(wsgi_remote)

        # make bodega and almacen
        bodegas = [
            Bodega(id=1, nombre='A'),
            Bodega(id=2, nombre='B'),
            ]
        stores = [
            Store(almacen_id=1, nombre="1", bodega_id=1),
            Store(almacen_id=2, nombre="2", bodega_id=2)]
        with cls.sessionmanager:
            list(map(cls.dbapi.create, bodegas))
            list(map(cls.dbapi.create, stores))

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

        with cls.sessionmanager:
            result, _ = validate_full_item(content, cls.dbapi)
            create_full_item_from_dict(cls.dbapi, content)
            cls.sessionmanager.session.commit()

    def test_create_inv(self):
        meta = InvMetadata()
        meta.codigo = 1
        meta.user = 'NA'
        meta.timestamp = datetime.datetime.now()
        meta.client = Client(codigo='asdf')
        meta.bodega_id = 1
        p = self.dbapi.search(PriceList)[0] 
        items = [Item(p, 1)]
        inv = Invoice(meta=meta, items=items)
        inv = self.invapi.save(inv)
        self.test_app.put('/api/nota/' + str(inv.meta.uid))

        ne = self.dbapi.search(NotaExtra)
        assert len(ne) == 1
        assert ne[0].id == inv.meta.uid
        assert ne[0].status == 'POSTEADO'

        ids = []
        def send_func(msg):
            print(msg)
            print('I aM HERE')
            resp = self.test_app_remote.post('/api2/remote_nota', msg)
            ids.append(resp.json['created'])
            return True
        # patch send to cloud's send
        start = meta.timestamp - datetime.timedelta(days=1)
        end = meta.timestamp + datetime.timedelta(days=1)
        send_to_cloud.send_to_remote(
                self.dbapi, self.invapi, start, end,
                send_func)
        ne = self.dbapi.getone(NotaExtra, id=1)
        self.assertEqual(ne.status, 'POSTEADO_')

        self.assertTrue(self.dbapi.get(1, SRINota) != None)

        self.test_app.delete('/api/nota/' + str(inv.meta.uid))
        ne = self.dbapi.getone(NotaExtra, id=1)
        assert ne.status == 'ELIMINADO'


if __name__ == '__main__':
    unittest.main()
