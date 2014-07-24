import json
import decimal

def json_dump(content):
    return json.dumps(
            content,
            cls=ModelEncoder,
            encoding='latin1')


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
    def serialize(self):
        return SerializableMixin._serialize_helper(self, self._name)

    @classmethod
    def deserialize(cls, dict_input):
        pass


    @staticmethod
    def _serialize_helper(obj, names):
        return {
            name: getattr(obj, name) for name in names
        }

    def to_json(self):
        return json.dumps(self.serialize(), cls=ModelEncoder)
