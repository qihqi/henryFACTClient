import unittest
from sqlalchemy import Integer, Column
from sqlalchemy.ext.declarative import declarative_base

from henry.base.dbapi import fieldcopy, dbmix


class DBApiTest(unittest.TestCase):

    def test_fieldcopy(self):

        class obj(object):
            pass

        data = {
            'field1': 'value1',
            'field2': 'value2',
            'field3': 'value3',
        }
        fields = ['field1', 'field2', 'field3']

        dest = {}
        fieldcopy(data, dest, fields)
        self.assertEquals(data, dest)

        dest2 = obj()
        fieldcopy(data, dest2, fields)
        self.assertEquals(data, dest2.__dict__)

        dest3 = {}
        fieldcopy(dest2, dest3, fields)
        self.assertEquals(data, dest3)

        dest4 = obj()
        fieldcopy(dest2, dest4, fields)
        self.assertEquals(data, dest4.__dict__)

    def test_dbmix(self):
        Base = declarative_base()
        class TestModel(Base):
            __tablename__ = 'test'
            key = Column(Integer, primary_key=True)
            value = Column(Integer)

        Wrapped = dbmix(TestModel)

        x = Wrapped()
        x.key = 1
        x.value = 2

        y = x.db_instance()
        self.assertEquals(type(y), TestModel)
        self.assertEquals(1, y.key)
        self.assertEquals(2, x.value)

        serialized = x.serialize()
        self.assertEquals({'key': 1, 'value': 2}, serialized)

if __name__ == '__main__':
    unittest.main()

