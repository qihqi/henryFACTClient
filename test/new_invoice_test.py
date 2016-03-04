import unittest
import sys
from henry.base.fileservice import FileService
from henry.dao.document import DocumentApi, PedidoApi
from henry.invoice.dao import Invoice
from henry.invoice.coreapi import make_nota_api
from henry.product.dao import PriceList, Store, ProdItem, ProdItemGroup
from test.testutils import make_test_dbapi, FakeTransaction
from webtest import TestApp


class InvoiceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        dbapi = make_test_dbapi()
        filemanager = FileService('/tmp')
        transaction = FakeTransaction()
        invapi = DocumentApi(dbapi.session, filemanager, transaction, Invoice)
        pedidoapi = PedidoApi(sessionmanager=dbapi.session, filemanager=filemanager)
        identity = lambda x: x
        wsgi = make_nota_api(
            '/api',
            dbapi,
            actionlogged=identity,
            invapi=invapi,
            auth_decorator=identity,
            pedidoapi=pedidoapi)
        cls.test_app = TestApp(wsgi)
        cls.dbapi = dbapi
        #insert some pricelist items

        with dbapi.session:
#            p1 = PriceList()
#            p1.precio1 = 150
#            p1.nombre = 'HILO ALGODON FINO'
#            p1.prod_id = 'HALGF'
#            p1.precio2 = 125
#            p1.threshold = 6000
#            p1.almacen_id = 1
#            dbapi.create(p1)
#            p2 = PriceList()
#            p2.almacen_id = 1
#            p2.precio1 = 50
#            p2.nombre = 'TERMINAL DE PULSERA MD.'
#            p2.prod_id = 'TPM'
#            p2.precio2 = 40
#            p2.threshold = 6000
#            dbapi.create(p2)
            alm = Store()
            alm.almacen_id = 3
            dbapi.create(alm)
            dbapi.db_session.commit()

    def test_create_invoice(self):
        inv1 = """
        {
                "items": [
                    {
                        "cant": 1000,
                        "prod": {
                            "precio1": 150,
                            "nombre": "HILO ALGODON FINO",
                            "codigo": "HALGF",
                            "precio2": 125,
                            "threshold": 6000
                        }
                    },
                    {
                        "cant": 4000,
                        "prod": {
                            "precio1": 50,
                            "nombre": "TERMINAL DE PULSERA MD.",
                            "codigo": "TPM",
                            "precio2": 40,
                            "threshold": 6000
                        }
                    }
                ],
                "meta": {
                    "retension": 0,
                    "codigo": "464138",
                    "paid_amount": 500,
                    "tax": 42,
                    "change": 0,
                    "discount": 0,
                    "client": {
                        "apellidos": "Consumidor Final",
                        "nombres": "",
                        "codigo": "NA",
                        "tipo": ""
                    },
                    "user": "karen",
                    "discount_percent": 0,
                    "almacen_id": 3,
                    "payment_format": "efectivo",
                    "total": 392,
                    "subtotal": 350,
                    "tax_percent": 12
                },
                "options": {
                    "incrementar_codigo": true,
                    "revisar_producto": true
                }
            }
        """

        resp = self.test_app.post('/api/nota', params=inv1)
        self.assertTrue('codigo' in resp.json)

        for x in self.dbapi.search(PriceList):
            print x.serialize()
        for x in self.dbapi.search(ProdItem):
            print x.serialize()
        for x in self.dbapi.search(ProdItemGroup):
            print x.serialize()


if __name__ == '__main__':
    unittest.main()
