import unittest
import datetime
from decimal import Decimal

from henry.importation.dao import InvMovementManager
from henry.users.dao import Client
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from henry.base.dbapi import DBApiGeneric
from henry.dao.transaction import TransactionApi, Transaction
from henry.dao.document import DocumentApi, Status, Item
from henry.inventory.dao import Transferencia, TransMetadata, TransType
from henry.invoice.dao import InvMetadata, Invoice
from henry.product.schema import NBodega
from henry.product.schema import NStore
from henry.schema.base import Base
from henry.base.fileservice import FileService
from henry.base.session_manager import SessionManager


class ProductApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        engine = create_engine('sqlite:///:memory:', echo=False)
        sessionfactory = sessionmaker(bind=engine)
        session = sessionfactory()
        Base.metadata.create_all(engine)
        cls.sessionmanager = SessionManager(sessionfactory)
        filemanager = FileService('/tmp')

        cls.prod_api = DBApiGeneric(cls.sessionmanager)
        cls.transaction_api = TransactionApi(cls.prod_api, '/tmp/transactions')
        cls.trans_api = DocumentApi(cls.sessionmanager, filemanager, cls.prod_api, Transferencia)
        cls.inv_api = DocumentApi(cls.sessionmanager, filemanager, cls.prod_api, Invoice)

        cls.productos = [
            ('0', 'prueba 0', Decimal('20.23'), Decimal('10'), 0),
            ('1', 'prueba 1', Decimal('20.23'), Decimal('10'), 0),
            ('2', 'prueba 2', Decimal('20.23'), Decimal('10'), 0),
            ('3', 'prueba 3', Decimal('20.23'), Decimal('10'), 0),
            ('4', 'prueba 4', Decimal('20.23'), Decimal('10'), 0),
            ('5', 'prueba 5', Decimal('20.23'), Decimal('10'), 0)]

        with cls.sessionmanager as s:
            b = NBodega(nombre='test1', nivel=0)
            s.add(b)
            store = NStore(nombre='store1', ruc='123')
            store.bodega = b
            s.add(store)
            store2 = NStore(nombre='store2', ruc='123')
            store2.bodega = b
            s.add(store2)
            s.commit()

        with cls.sessionmanager:
            for p in cls.productos:
                pass

    def test_get_producto(self):
        with self.sessionmanager:
            x = self.prod_api.get_producto('0')
            y = self.prod_api.get_producto('0', almacen_id=1)

            self.assertEqual(x.nombre, 'prueba 0')
            self.assertEqual(y.precio1, 20)
            self.assertEqual(y.threshold, 0)

    def test_search(self):
        with self.sessionmanager:
            prods = self.prod_api.search_producto('prueba')
            self.assertEquals(6, len(list(prods)))
            for x in prods:
                self.assertTrue(x.nombre.startswith('prueba'))

    def test_search_full(self):
        with self.sessionmanager:
            prods = self.prod_api.search_producto('prueba', almacen_id=1)
            assert len(list(prods)) == 6
            for x in prods:
                self.assertTrue(x.nombre.startswith('prueba'))
                self.assertTrue(x.precio1 == 20)
                self.assertTrue(x.precio2 == 10)

    def test_transaction(self):
        with self.sessionmanager:
            prod = self.prod_api.get_producto('0', bodega_id=1)
            starting = prod.cantidad
            t = Transaction(bodega_id=1, prod_id='0', name=prod.nombre, delta=10, ref='test')
            d = self.prod_api.execute_transactions([t])
        with self.sessionmanager:
            prod = self.prod_api.get_producto('0', bodega_id=1)
            self.assertEquals(10, prod.cantidad - starting)

    def test_ingress(self):
        with self.sessionmanager:
            init_prod_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad
            t = TransMetadata(
                origin=None,
                dest=1,
                user=0,
                trans_type=TransType.INGRESS,
                ref='hello world')
            items = [Item(self.prod_api.get_producto('1'), 10),
                     Item(self.prod_api.get_producto('2'), 10)]
            transfer = Transferencia(t, items)
            trans = self.trans_api.save(transfer)
            self.assertEquals(t.status, Status.NEW)

        with self.sessionmanager:
            trans = self.trans_api.commit(trans)
            self.assertEquals(trans.meta.status, Status.COMITTED)

        with self.sessionmanager:
            post_prod_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad
            self.assertEquals(Decimal(10), post_prod_cant - init_prod_cant)

        with self.sessionmanager:
            trans = self.trans_api.delete(trans)
        with self.sessionmanager:
            last_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad
            self.assertEquals(trans.meta.status, Status.DELETED)
            self.assertEquals(init_prod_cant, last_cant)

    def test_transfer(self):
        with self.sessionmanager:
            init_prod_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad
            t = TransMetadata(
                origin=2,
                dest=1,
                user=0,
                trans_type=TransType.TRANSFER,
                ref='hello world')
            items = [Item(self.prod_api.get_producto('1'), 10)]
            transfer = Transferencia(t, items)
            trans = self.trans_api.save(transfer)

            self.assertEquals(t.status, Status.NEW)
            trans = self.trans_api.commit(trans)
            self.assertEquals(trans.meta.status, Status.COMITTED)
            post_prod_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad
            self.assertEquals(Decimal(10), post_prod_cant - init_prod_cant)

            trans = self.trans_api.delete(trans)
            last_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad
            self.assertEquals(trans.meta.status, Status.DELETED)
            self.assertEquals(init_prod_cant, last_cant)

    def test_inv(self):
        with self.sessionmanager:
            init_prod_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad

            client = Client()
            client.codigo = '123'

            t = InvMetadata(
                client=client,
                codigo='123',
                user='asdf',
                total=123,
                subtotal=123,
                tax=123,
                discount=0,
                bodega_id=1,
                almacen_id=1
            )
            inv = Invoice()
            inv.meta = t
            inv.items = [
                Item(self.prod_api.get_producto('1'), 5)
            ]
            invoice = self.inv_api.save(inv)
            self.assertEquals(self.inv_api.get_doc(invoice.meta.uid).meta.codigo, '123')

            x = self.inv_api.commit(invoice)
            self.assertEquals(Status.COMITTED, x.meta.status)
            new_inv = self.prod_api.get_producto('1', bodega_id=1).cantidad
            self.assertEquals(-5, new_inv - init_prod_cant)

            x = self.inv_api.delete(invoice)
            self.assertEquals(Status.DELETED, x.meta.status)
            new_inv = self.prod_api.get_producto('1', bodega_id=1).cantidad
            self.assertEquals(0, new_inv - init_prod_cant)

            today = datetime.datetime.now()
            yesterday = today - datetime.timedelta(days=1)
            searched = list(self.inv_api.search_metadata_by_date_range(start=yesterday, end=today))
            print searched
            self.assertEquals(1, len(searched))


if __name__ == '__main__':
    unittest.main()
