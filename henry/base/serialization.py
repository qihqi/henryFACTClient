import datetime
import decimal
import json
import re

# encoding of the database
DB_ENCODING = 'latin1'


def decode(s, codec=DB_ENCODING):
    if s is None:
        return None
    return s.decode(codec)


def json_dumps(content):
    return json.dumps(
        content,
        cls=ModelEncoder,
        encoding=DB_ENCODING)


def parse_iso_date(datestring):
    return datetime.datetime(*map(int, re.split('[^\d]', datestring)[:-1]))


def json_loads(content):
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
            return names.items()
        else:
            return map(lambda x: (x, x), names)

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
                setattr(y, thisname, value)
        return y


class SerializableMixin(object):
    _name = ()

    def merge_from(self, obj):
        for key in self._name:
            their = getattr(obj, key, None) or obj.get(key, None) 
            mine = getattr(self, key)
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
