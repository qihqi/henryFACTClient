import json
import decimal
import datetime

# encoding of the database
DB_ENCODING = 'latin1'

def decode(s, codec=DB_ENCODING):
    if s is None:
        return None
    return s.decode(codec)


def json_dump(content):
    return json.dumps(
            content,
            cls=ModelEncoder,
            encoding=DB_ENCODING)


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
    @classmethod
    def _get_name_pairs(cls, names):
        if isinstance(names, dict):
            return names.items()
        else:
            return map(lambda x: (x, x), names) 

    def db_instance(self):
        x = self._db_class()
        for thisname, dbname in DbMixin._get_name_pairs(self._db_attr):
            if not thisname in self._excluded_vars: 
                value = getattr(self, thisname, None)
                if value is not None:
                    setattr(x, dbname, value)
        return x 

    @classmethod 
    def from_db_instance(cls, db_instance):
        y = cls()
        for thisname, dbname in self._get_name_pairs(self._db_attr):
            if not thisname in self._excluded_vars: 
                value = getattr(db_instance, dbname, None)
                if value is not None:
                    setattr(y, thisname, value)
        return y


class SerializableMixin(object):

    def merge_from(self, obj):
        for key in self._name:
            try:
                setattr(self, key, getattr(obj, key))
            except AttributeError:
                try:
                    setattr(self, key, obj[key])
                except:
                    pass
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
        return json_dump(self.serialize())
