import json
import decimal

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
        return super(ModelEncoder, self).default(obj)


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
        obj = cls()
        obj.__dict__ = {key: val for key, val in dict_input.items() if key in cls._name}


    @staticmethod
    def _serialize_helper(obj, names):
        return {
            name: getattr(obj, name) for name in names if getattr(obj, name) is not None
        }

    def to_json(self):
        return json.dumps(self.serialize(), cls=ModelEncoder)
