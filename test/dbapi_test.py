import dataclasses
import unittest
from typing import Optional

from sqlalchemy import Integer, Column
from sqlalchemy.ext.declarative import declarative_base

from henry.base.dbapi import SerializableDB
from base.serialization import fieldcopy


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
        self.assertEqual(data, dest)

        dest2 = obj()
        fieldcopy(data, dest2, fields)
        self.assertEqual(data, dest2.__dict__)

        dest3 = {}
        fieldcopy(dest2, dest3, fields)
        self.assertEqual(data, dest3)

        dest4 = obj()
        fieldcopy(dest2, dest4, fields)
        self.assertEqual(data, dest4.__dict__)

    def test_dbmix(self):
        Base = declarative_base()
        class TestModel(Base):
            __tablename__ = 'test'
            key = Column(Integer, primary_key=True)
            value = Column(Integer)

        @dataclasses.dataclass
        class Wrapped(SerializableDB[TestModel]):
            db_class = TestModel
            key: Optional[int] = None
            value: Optional[int] = None

        x = Wrapped(1, 2)

        y = x.db_instance()
        self.assertEqual(type(y), TestModel)
        self.assertEqual(1, y.key)
        self.assertEqual(2, x.value)

        from_db = Wrapped.from_db_instance(y)
        self.assertEqual(x, from_db)

        serialized = x.serialize()
        self.assertEqual({'key': 1, 'value': 2}, serialized)

        des = Wrapped.deserialize(serialized)
        self.assertEqual(x, des)


if __name__ == '__main__':
    unittest.main()

