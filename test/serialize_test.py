import dataclasses
import json
import unittest
import datetime
from typing import Optional, List

from henry.base.serialization import SerializableData


class SerializeTest(unittest.TestCase):

    def test_serialize1(self):

        @dataclasses.dataclass
        class DataObj(SerializableData):
            a: Optional[datetime.datetime] = None
            b: Optional[datetime.date] = None

        x = DataObj()
        x.b = datetime.date(2000, 1, 1)
        x.a = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        ser = x.to_json()
        newx = DataObj.deserialize(json.loads(ser))
        self.assertEqual(newx, x)

    def test_serialize_nested(self):

        @dataclasses.dataclass
        class DataObj(SerializableData):
            a: Optional[datetime.datetime] = None
            b: Optional[datetime.date] = None

        @dataclasses.dataclass
        class DataObj2(SerializableData):
            c: DataObj

        x = DataObj()
        x.b = datetime.date(2000, 1, 1)
        x.a = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)

        y = DataObj2(c=x)
        ser = y.to_json()
        newy = DataObj2.deserialize(json.loads(ser))
        self.assertIsInstance(newy.c, DataObj)
        self.assertEqual(newy, y)

        @dataclasses.dataclass
        class DataObj3(SerializableData):
            c: List[DataObj] = dataclasses.field(default_factory=lambda: [])

        y = DataObj3()
        y.c.append(x)
        ser = y.to_json()
        newy = DataObj3.deserialize(json.loads(ser))
        self.assertIsInstance(newy.c[0], DataObj)
        self.assertEqual(newy, y)

if __name__ == '__main__':
    unittest.main()
