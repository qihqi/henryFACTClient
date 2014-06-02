import json
import unittest
import sqlalchemy
from henry.layer2.models import Producto, Venta, Factura, ModelEncoder
from henry.layer1.schema import Base
from henry import config


class ProductoTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config.CONFIG['connection_string'] = 'sqlite:///:memory:'
        config.get_engine.engine = None
        Base.metadata.create_all(config.get_engine())
        cls.productos = [
            Producto('0', 'prueba 0', 20, 10, 0),
            Producto('1', 'prueba 1', 20, 10, 0),
            Producto('2', 'prueba 2', 20, 10, 0),
            Producto('3', 'prueba 3', 20, 10, 0),
            Producto('4', 'prueba 4', 20, 10, 0),
            Producto('5', 'prueba 5', 20, 10, 0)]
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
        print json.dumps(v2.serialize(), cls=ModelEncoder)

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
        print json.dumps(f2.serialize(), cls=ModelEncoder)



if __name__ == '__main__':
    unittest.main()
