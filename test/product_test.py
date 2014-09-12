import unittest
import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from henry.layer1.schema import NProducto, NContenido, Base
from henry.helpers.fileservice import FileService
from henry.layer2.productos import Product, ProductApiDB, Transaction, TransApiDB, Transferencia, TransType, Metadata
from henry.layer2.documents import Status, DocumentCreationRequest
from henry.layer2.invoice import Invoice, InvMetadata, InvApiDB

class ProductApiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        engine = create_engine('sqlite:///:memory:', echo=True)
        session = sessionmaker(bind=engine)()
        Base.metadata.create_all(engine)
        cls.productos = [
            ('0', 'prueba 0', Decimal('20.23'), Decimal('10'), 0),
            ('1', 'prueba 1', Decimal('20.23'), Decimal('10'), 0),
            ('2', 'prueba 2', Decimal('20.23'), Decimal('10'), 0),
            ('3', 'prueba 3', Decimal('20.23'), Decimal('10'), 0),
            ('4', 'prueba 4', Decimal('20.23'), Decimal('10'), 0),
            ('5', 'prueba 5', Decimal('20.23'), Decimal('10'), 0)]
        for p in cls.productos:
            codigo, nombre, p1, p2, thres = p
            x = NProducto(codigo=codigo, nombre=nombre)
            x.contenidos.append(
                NContenido(prod_id=codigo, precio=p1, precio2=p2, cant_mayorista=thres,
                           bodega_id=1, cant=0))
            x.contenidos.append(
                NContenido(prod_id=codigo, precio=p1, precio2=p2, cant_mayorista=thres,
                           bodega_id=2, cant=0))
            session.add(x)
        result = session.commit()
        filemanager = FileService('/tmp')
        cls.prod_api = ProductApiDB(session)
        cls.trans_api = TransApiDB(session, filemanager, cls.prod_api)
        cls.inv_api = InvApiDB(session, filemanager, cls.prod_api)

    def test_get_producto(self):
        x = self.prod_api.get_producto('0')
        y = self.prod_api.get_producto('0', almacen_id=1)

        self.assertEqual(x.nombre, 'prueba 0')
        self.assertEqual(y.precio1, Decimal('20.23'))
        self.assertEqual(y.threshold, 0)

    def test_search(self):
        prods = self.prod_api.search_producto('prueba')
        assert len(list(prods)) == 6
        for x in prods:
            self.assertTrue(x.nombre.startswith('prueba'))

    def test_search_full(self):
        prods = self.prod_api.search_producto('prueba', almacen_id=1)
        assert len(list(prods)) == 6
        for x in prods:
            self.assertTrue(x.nombre.startswith('prueba'))
            self.assertTrue(x.precio1 == Decimal('20.23'))
            self.assertTrue(x.precio2 == Decimal('10'))

    def test_transaction(self):
        starting = self.prod_api.get_producto('0', bodega_id=1).cantidad
        t = Transaction(prod_id='0', bodega_id=1, delta=10)
        d = self.prod_api.execute_transactions([t])
        prod = self.prod_api.get_producto('0', bodega_id=1)
        self.assertEquals(10, prod.cantidad - starting)

    def test_ingress(self):
        init_prod_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad
        t = Metadata(
                origin=1,
                dest=1,
                user=0,
                trans_type=TransType.INGRESS,
                ref='hello world')
        req = DocumentCreationRequest(t)
        req.add('1' , 10)
        req.add('2' , 10)

        trans = self.trans_api.save(req)
        self.assertEquals(t.status, Status.NEW)
        trans = self.trans_api.commit(trans.meta.uid)
        self.assertEquals(trans.meta.status, Status.COMITTED)
        post_prod_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad
        self.assertEquals(Decimal(10), post_prod_cant - init_prod_cant)
        trans = self.trans_api.delete(trans.meta.uid)
        last_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad
        self.assertEquals(trans.meta.status, Status.DELETED)
        self.assertEquals(init_prod_cant, last_cant)

    def test_transfer(self):
        init_prod_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad
        t = Metadata(
                origin=2,
                dest=1,
                user=0,
                trans_type=TransType.TRANSFER,
                ref='hello world')
        req = DocumentCreationRequest(t)
        req.add('1' , 10)

        trans = self.trans_api.save(req)
        self.assertEquals(t.status, Status.NEW)
        trans = self.trans_api.commit(trans.meta.uid)
        self.assertEquals(trans.meta.status, Status.COMITTED)
        post_prod_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad
        self.assertEquals(Decimal(10), post_prod_cant - init_prod_cant)

        trans = self.trans_api.delete(trans.meta.uid)
        last_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad
        self.assertEquals(trans.meta.status, Status.DELETED)
        self.assertEquals(init_prod_cant, last_cant)


    def test_inv(self):
        init_prod_cant = self.prod_api.get_producto('1', bodega_id=1).cantidad

        t = InvMetadata(
                client='asdf',
                codigo=None,
                user='asdf',
                total=123,
                subtotal=123,
                tax=123,
                discount=0,
                bodega=1,
                almacen=1
                )
        inv = DocumentCreationRequest()
        inv.meta = t
        inv.items = [
                ('1', 'name', 5, 0.01)
                ]
        invoice = self.inv_api.save(inv)
        print invoice.meta.uid
        self.inv_api.set_codigo(invoice.meta.uid, '123')
        self.assertEquals(self.inv_api.get_doc(invoice.meta.uid).meta.codigo, '123')

        doc = self.inv_api.get_doc_by_codigo(alm=1, codigo='123')
        self.assertEquals(invoice.meta.uid, doc.meta.uid)

        x = self.inv_api.commit(invoice.meta.uid)
        self.assertEquals(Status.COMITTED, x.meta.status)
        new_inv = self.prod_api.get_producto('1', bodega_id=1).cantidad
        self.assertEquals(-5, new_inv - init_prod_cant)

        x = self.inv_api.delete(invoice.meta.uid)
        self.assertEquals(Status.DELETED, x.meta.status)
        new_inv = self.prod_api.get_producto('1', bodega_id=1).cantidad
        self.assertEquals(0, new_inv - init_prod_cant)

        now = datetime.datetime.now()
        tomorrow = now + datetime.timedelta(days=1)
        all_inv = list(self.inv_api.get_dated_report(
                start_date=now.date(),
                end_date=tomorrow.date(),
                almacen=1, status=None))
        self.assertEquals(1, len(all_inv))
        all_inv = list(self.inv_api.get_dated_report(
                start_date=now.date(),
                end_date=tomorrow.date(),
                almacen=1))
        self.assertEquals(0, len(all_inv))

        all_inv = list(self.inv_api.get_dated_report(
                start_date=now.date(),
                end_date=tomorrow.date(),
                almacen=1, status=[Status.COMITTED, Status.DELETED]))
        self.assertEquals(1, len(all_inv))




if __name__ == '__main__':
    unittest.main()
