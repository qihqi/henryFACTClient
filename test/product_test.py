import unittest
import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from henry.layer1.schema import NProducto, NContenido, Base, TransType, Status
from henry.helpers.fileservice import FileService
from henry.layer2.productos import Product, ProductApiDB, Transaction, TransApiDB, Transferencia

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
            session.add(x)
        result = session.commit()
        filemanager = FileService('/tmp')
        cls.prod_api = ProductApiDB(session)
        cls.trans_api = TransApiDB(session, filemanager, cls.prod_api)

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
        starting = self.prod_api.get_producto('0', bodega_id=0).cantidad
        t = Transaction(prod_id='0', bodega_id=0, delta=10)
        d = self.prod_api.execute_transactions([t, Transaction(prod_id='123', bodega_id=0, delta=1)])
        prod = self.prod_api.get_producto('0', bodega_id=1)
        self.assertEquals(10, prod.cantidad - starting)

    def test_transfer(self):
        init_prod_cant = self.prod_api.get_producto('0', bodega_id=1).cantidad
        t = Transferencia(
                uid='1',
                origin=1,
                dest=1,
                user=0,
                trans_type=TransType.INGRESS,
                ref='hello world',
                timestamp=datetime.datetime.now())
        t.items = (
                (1, '0', 1),
                (1, '1', 1),
                )
        t = self.trans_api.save(t)
        self.assertEquals(t.status, Status.NEW)
        result = self.trans_api.commit(t)
        self.assertEquals(t.status, Status.COMITTED)
        post_prod_cant = self.prod_api.get_producto('0', bodega_id=1).cantidad
        self.assertEquals(Decimal(1), post_prod_cant - init_prod_cant)
        x =  self.trans_api.get_doc('1')
        print x.serialize()



if __name__ == '__main__':
    unittest.main()
