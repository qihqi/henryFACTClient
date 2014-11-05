import unittest
import datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from henry.layer1.schema import NProducto, NContenido, Base
from henry.helpers.fileservice import FileService
from henry.layer2.client import Client, ClientApiDB
from henry.layer1.session_manager import SessionManager

class ClientTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        engine = create_engine('sqlite:///:memory:', echo=True)
        sessionfactory = sessionmaker(bind=engine)
        session = sessionfactory()
        Base.metadata.create_all(engine)
        cls.clientes= [
            Client(codigo='123',
                   nombres='nombre1 nombre2',
                   apellidos='apellido1 apellido2',
                   direccion='direccion',
                   telefono='12345567',
                   ciudad='ciudad',
                   tipo=1,
                   cliente_desde=datetime.date.today()
            )
        ]
        for c in cls.clientes:
            session.add(c)
        result = session.commit()
        cls.sessionmanager = SessionManager(sessionfactory)
        cls.clientapi = ClientApiDB(cls.sessionmanager)

    def test_get_cliente(self):
        with self.sessionmanager:
            x = self.clientapi.get('123')
            self.assertEqual(x.codigo, '123')

    def test_create(self):
        c = Client(codigo='345',
               nombres='nombre1 nombre2',
               apellidos='apellido1 apellido2',
               direccion='direccion',
               telefono='12345567',
               ciudad='ciudad',
               tipo=1,
               cliente_desde=datetime.date.today())
        with self.sessionmanager:
            self.clientapi.save(c)
        with self.sessionmanager:
            x = list(self.clientapi.search('a'))
            for i in x:
                print i.serialize()
            self.assertEquals(2, len(x))
            
            
if __name__ == '__main__':
    unittest.main()

