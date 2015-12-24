import unittest
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from henry.schema.base import Base
from henry.base.fileservice import FileService
from henry.accounting.dao import PaymentApi, Check
from henry.dao import (DocumentApi, Invoice,
                       TransactionApi)
from henry.base.session_manager import SessionManager


class ProductApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        engine = create_engine('sqlite:///:memory:', echo=False)
        sessionfactory = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)
        cls.sessionmanager = SessionManager(sessionfactory)
        cls.paymentapi = PaymentApi(cls.sessionmanager)
        filemanager = FileService('/tmp')
        transaction = TransactionApi(cls.sessionmanager, filemanager)
        invapi = DocumentApi(cls.sessionmanager, filemanager, transaction, Invoice)
        inv = Invoice.deserialize({
            'meta': {
                'client': {
                   'codigo': 'NA'
                },
                'total': 123,
                'subtotal': 123,
                'tax' : '1',
                'user_id': 'yu',
                'codigo': str('123'),
                'almacen_id': 1,
            },
            'items': []
            })
        with cls.sessionmanager:
            inv = invapi.save(inv)
        cls.uid = inv.meta.uid  # id to refer for payment


    def test_save_and_get(self):
        check = Check(
            accountno='124',
            bank='bank',
            checkno=1,
            holder='holder',
            checkdate=datetime.date.today(),
            note_id=self.uid,
            client_id='NA',
            value=100,
            date=datetime.date.today(),
        )
        with self.sessionmanager:
            uid = self.paymentapi.save_check(check)

        with self.sessionmanager:
            check2 = self.paymentapi.get_check(uid)
            for x in check._name:
                if x in ('status', 'uid'):
                    continue
                old = getattr(check, x, None)
                new = getattr(check2, x, None)
                assert old == new, (old, new, x)


if __name__ == '__main__':
    unittest.main()
