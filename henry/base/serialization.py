import datetime
import decimal
import json
from operator import itemgetter
import re
from typing import Dict

# encoding of the database
DB_ENCODING = 'latin1'


def decode(s):
    if s is None:
        return None
    try:
        return s.decode('utf-8')
    except UnicodeDecodeError:
        return s.decode('latin1')


def json_dumps(content: Dict) -> str:
    return json.dumps(content, cls=ModelEncoder)


def parse_iso_datetime(datestring: str) -> datetime.datetime:
    return datetime.datetime(*list(map(int, re.split('[^\d]', datestring))))  # type: ignore

def parse_iso_date(datestring: str) -> datetime.date:
    return datetime.date(*list(map(int, datestring.split('-'))))  # type: ignore

def json_loads(content: str) -> Dict:
    return json.loads(content, encoding=DB_ENCODING)


class ModelEncoder(json.JSONEncoder):
    def __init__(self, use_int_repr=False, decimal_places=2, *args, **kwargs):
        super(ModelEncoder, self).__init__(*args, **kwargs)
        self.use_int_repr = use_int_repr
        self.decimal_places = decimal_places

    def default(self, obj):
        if hasattr(obj, 'serialize'):
            return obj.serialize()
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return super(ModelEncoder, self).default(obj)


class DbMixin(object):
    _db_class = None
    _db_attr = ()

    @classmethod
    def _get_name_pairs(cls, names):
        if isinstance(names, dict):
            return list(names.items())
        else:
            return [(x, x) for x in names]

    def db_instance(self):
        x = self._db_class()
        excluded = getattr(self, '_excluded_vars', [])
        for thisname, dbname in DbMixin._get_name_pairs(self._db_attr):
            if thisname not in excluded:
                value = getattr(self, thisname, None)
                if value is not None:
                    setattr(x, dbname, value)
        return x

    @classmethod
    def from_db_instance(cls, db_instance):
        y = cls()
        excluded = getattr(cls, '_excluded_vars', [])
        for thisname, dbname in cls._get_name_pairs(cls._db_attr):
            if thisname not in excluded:
                value = getattr(db_instance, dbname, None)
                if isinstance(value, bytes):
                    value = decode(value)
                setattr(y, thisname, value)
        return y


def extract_obj_fields(obj, names):
    return {
        name: getattr(obj, name) for name in names if getattr(obj, name, None) is not None
        }


class TypedSerializableMixin(object):
    _fields = ()
    _natural_fields = (int, float, str, str)

    def __init__(self, **kwargs):
        for x, const in self._fields:
            val = kwargs.get(x, None)
            if val is not None:
                setattr(self, x, val)

    def merge_from_obj(self, obj):
        for x, const in self._fields:
            val = getattr(obj, x)
            if val is not None:
                setattr(self, x, val)
        return self

    def merge_from_dict(self, thedict):
        for x, const in self._fields:
            val = thedict.get(x, None)
            if val is not None:
                if (const not in self._natural_fields or
                        not isinstance(x, const)):
                    val = const(val)
            if val is not None or not hasattr(self, x):
                setattr(self, x, val)
        return self

    def serialize(self):
        return extract_obj_fields(self, list(map(itemgetter(0), self._fields)))

    @classmethod
    def deserialize(cls, thedict):
        return cls().merge_from_dict(thedict)


class SerializableMixin(object):
    _name = ()

    def merge_from(self, obj):
        for key in self._name:
            their = getattr(obj, key, None)
            if their is None and hasattr(obj, 'get'):  # merge from dict
                their = obj.get(key, None)
            mine = getattr(self, key, None)
            if isinstance(their, bytes):
                their = decode(their)
            setattr(self, key, their or mine)  # defaults to theirs
        return self

    def serialize(self):
        return SerializableMixin._serialize_helper(self, self._name)

    @classmethod
    def deserialize(cls, dict_input):
        return cls().merge_from(dict_input)

    @staticmethod
    def _serialize_helper(obj, names):
        return {
            name: getattr(obj, name) for name in names if getattr(obj, name, None) is not None
        }

    def to_json(self):
        return json_dumps(self.serialize())
