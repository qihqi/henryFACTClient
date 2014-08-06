import json
import datetime
import unittest
import sqlalchemy
from decimal import Decimal
from henry.layer2.models import (Producto, Venta, Factura,
    Cliente)
from henry.layer1.schema import Base
from henry import config
from henry.helpers.serialization import ModelEncoder


class ProductoTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.CONFIG['connection_string'] = 'sqlite:///:memory:'
        config.get_engine.engine = None
        config.CONFIG['echo'] = False
        Base.metadata.create_all(config.get_engine())
        cls.productos = [
            Producto('0', 'prueba 0', Decimal('20.23'), Decimal('10'), 0),
            Producto('1', 'prueba 1', Decimal('20.23'), Decimal('10'), 0),
            Producto('2', 'prueba 2', Decimal('20.23'), Decimal('10'), 0),
            Producto('3', 'prueba 3', Decimal('20.23'), Decimal('10'), 0),
            Producto('4', 'prueba 4', Decimal('20.23'), Decimal('10'), 0),
            Producto('5', 'prueba 5', Decimal('20.23'), Decimal('10'), 0)]
        for p in cls.productos:
            Producto.save(p, 1)

    @classmethod
    def tearDownClass(cls):
        engine = config.get_engine()
        meta = sqlalchemy.MetaData(engine)
        meta.reflect()
        meta.drop_all()

    def _equal_prod(self, prod1, prod2):
        self.assertEquals(prod1.codigo, prod2.codigo)
        self.assertEquals(prod1.nombre, prod2.nombre)
        self.assertEquals(prod1.precio1, prod2.precio1)
        self.assertEquals(prod1.precio2, prod2.precio2)
        self.assertEquals(prod1.threshold, prod2.threshold)

    def test_search(self):
        p = list(Producto.search('p', 1))
        self.assertEquals(6, len(p))
        for x, y in zip(p, self.productos):
            self._equal_prod(y, x)

    def test_create_producto(self):
        for codigo in range(6):
            p = Producto.get(str(codigo), 1)
            self._equal_prod(self.productos[codigo], p)

    def test_venta(self):
        venta = Venta('NA', 1,
                      items=[
                          (1, Producto('0')),
                          (2, Producto('1'))
                      ])
        Venta.save(venta)
        v2 = Venta.get(venta.id)
        self.assertEquals(2, len(v2.items))
        self.assertEquals('0', v2.items[0][1].codigo)
        self.assertEquals('1', v2.items[1][1].codigo)
        self.assertEquals(1, v2.items[0][0])
        self.assertEquals(2, v2.items[1][0])

    def test_factura(self):
        factura = Factura('NA', 1,
                      items=[
                          (1, Producto('0', precio1=0.01)),
                          (2, Producto('1', precio2=0.02))
                      ])
        factura.codigo = 123
        factura.bodega_id = 1
        Factura.save(factura)
        f2 = Factura.get_with_bodega(factura.codigo, factura.bodega_id)

        self.assertEquals(2, len(f2.items))
        self.assertEquals('0', f2.items[0][1].codigo)
        self.assertEquals('1', f2.items[1][1].codigo)
        self.assertEquals(1, f2.items[0][0])
        self.assertEquals(2, f2.items[1][0])

    def test_cliente(self):
        cliente = Cliente()
        cliente.nombres = 'han'
        cliente.apellidos = 'hola que tal'
        cliente.direccion = 'hello'
        cliente.ciudad = 'ciudad'
        cliente.telefono = 'hello'
        cliente.tipo = 'hello'
        cliente.codigo = '123'
        cliente.cliente_desde = datetime.datetime.now()
        Cliente.save(cliente)

        c2 = Cliente.get('123')

        print json.dumps(Cliente.get('123'), cls=ModelEncoder)
        print json.dumps(Cliente.search('hola'), cls=ModelEncoder)

if __name__ == '__main__':
    unittest.main()
