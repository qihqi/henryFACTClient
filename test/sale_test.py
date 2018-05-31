import datetime
import unittest
from decimal import Decimal

from henry.base.fileservice import FileService
from henry.base.serialization import json_dumps
from henry.dao.document import Status
from henry.importation.dao import Sale
from henry.sale_records.dao import InvMovementManager, Sale
from henry.importation.web import make_import_apis
from henry.invoice.dao import PaymentFormat
from henry.product.dao import InventoryApi
from test.testutils import make_test_dbapi
from webtest import TestApp


class InvoiceTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        dbapi = make_test_dbapi()
        fileservice = FileService('/tmp')
        inventoryapi = InventoryApi('/tmp')
        auth_decorator = lambda x: x
        invmomanager = InvMovementManager(dbapi, fileservice, inventoryapi)
        wsgi = make_import_apis('/import', auth_decorator, dbapi, invmomanager)
        cls.test_app = TestApp(wsgi)
        cls.dbapi = dbapi

    def test_create_invoice(self):
        sale = Sale()
        sale.timestamp = datetime.datetime(2015, 1, 1, 0, 0, 0)
        sale.client_id = 'NA'
        sale.seller_codename = 'boya'
        sale.seller_ruc = '123'
        sale.seller_inv_uid = 1
        sale.invoice_code = '123'
        sale.pretax_amount_usd = Decimal('123')
        sale.tax_usd = Decimal('123')
        sale.status = Status.NEW
        sale.user_id = 'yu'
        sale.payment_format = PaymentFormat.CASH

        result = self.test_app.post('/import/client_sale', params=json_dumps(sale))
        self.assertEquals(200, result.status_code)

        sales = list(self.dbapi.search(Sale))
        self.assertEquals(1, len(sales))
        self.assertEquals(sale.timestamp, sales[0].timestamp)
        self.assertEquals(Status.NEW, sales[0].status)

        result = self.test_app.delete('/import/client_sale', params=json_dumps(sale))
        self.assertEquals(200, result.status_code)
        self.assertEquals(1, result.json['deleted'])
        sales = list(self.dbapi.search(Sale))
        self.assertEquals(1, len(sales))
        self.assertEquals(sale.timestamp, sales[0].timestamp)
        self.assertEquals(Status.DELETED, sales[0].status)


if __name__ == '__main__':
    unittest.main()
