import unittest
from henry.layer2.models import Producto
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


if __name__ == '__main__':
    unittest.main()
