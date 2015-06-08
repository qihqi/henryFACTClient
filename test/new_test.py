import time
import unittest
from henry.base.schema import NProducto, NContenido
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class SpeedTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('mysql+mysqldb://root:no jodas@localhost/henry')
        self.sessionmaker = sessionmaker(bind=self.engine)

    def test_1query(self):

        session = self.sessionmaker()
        start = time.time()
        result = session.query(NProducto, NContenido).filter(NContenido.prod_id == NProducto.codigo).filter(
            NProducto.codigo == 'AAAA')
        for x in result:
            print x.__dict__
        end = time.time()
        print '1 query ', end - start

    def test_1query2(self):

        session = self.sessionmaker()
        start = time.time()
        result = session.query(NProducto, NContenido).filter(NContenido.prod_id == NProducto.codigo).filter(
            NProducto.codigo == 'AAAA')
        for x in result:
            print x.__dict__
        end = time.time()
        print '1 query ', end - start

    def test_2query(self):

        session = self.sessionmaker()
        start = time.time()
        result1 = session.query(NProducto).filter(NProducto.nombre.startswith('a'))
        for x in result1:
            print x.__dict__
        end = time.time()
        print '2 query ', end - start

    def atest_join(self):
        session = self.sessionmaker()
        start = time.time()
        result = session.query(NProducto).join(NContenido, NContenido.prod_id == NProducto.codigo).filter(
            NProducto.nombre.startswith('a'))
        for x in result:
            print x.__dict__
        end = time.time()
        print 'join query ', end - start


if __name__ == '__main__':
    unittest.main()
