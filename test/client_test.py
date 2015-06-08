import unittest
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from henry.base.schema import Base
from henry.layer2.client import Client, ClientApiDB
from henry.base.session_manager import SessionManager
from henry.config import validate_uid_and_ruc


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


    def test_validate_cedula(self):
        test_false = [
            '1302576771001',
            '1302576771001',
            '0910558795',
            '0910558795',
            '0992185888',
            '0992185888',
            '0930174717',
            '0930174717',
            '0906426646',
            '0906426646',
            '0912254474001',
            '0912254474001',
            '0900518843',
            '0900518843',
            '1708898789001',
            '1708898789001',
            '0901480778001',
            '0901480778001',
            '1203165151',
            '1203165151',
            '1729984507',
            '1729984507',
            '0921404016',
            '0921404016',
            '1101033250',
            '1101033250',
            '0926418753',
            '0926418753',
            '1302576771',
            '1302576771',
        ]
        for x in test_false:
            self.assertFalse(validate_uid_and_ruc(x))
            
            
if __name__ == '__main__':
    unittest.main()
