import datetime
import decimal
import json
import unicodedata
from operator import itemgetter
import re
from typing import Dict, Tuple, TypeVar, Type, Generic, Union, Any, Callable

# encoding of the database
from henry.base.interface import SerializableInterface

DB_ENCODING = 'latin1'


def decode(s):
    if s is None:
        return None
    try:
        return s.decode('utf-8')
    except UnicodeDecodeError:
        return s.decode('latin1')


def json_dumps(content) -> str:
    return json.dumps(content, cls=ModelEncoder)


def parse_iso_datetime(datestring: str) -> datetime.datetime:
    return datetime.datetime(*list(map(int, re.split('[^\d]', datestring))))  # type: ignore

def parse_iso_date(datestring: str) -> datetime.date:
    return datetime.date(*list(map(int, datestring.split('-'))))  # type: ignore


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


def extract_obj_fields(obj, names):
    return {
        name: getattr(obj, name) for name in names if getattr(obj, name, None) is not None
        }


T = TypeVar('T', bound='SerializableData')
class SerializableData(SerializableInterface):
    """Meant to be subclassed by a class with @dataclass decorator.

    Adds methods to support converting to / from dicts
    """
    def __init__(self, **kwargs):
        self.merge_from(kwargs)

    def merge_from(self: T, obj: Any) -> T:
        fieldcopy(src=obj, dest=self,
                  fields=self.__dataclass_fields__.keys())  # type: ignore
        return self

    def serialize(self) -> Dict[str, Any]:
        """Respects renaming or / and skipping."""
        res = {}
        for field in self.__dataclass_fields__.values():  # type: ignore
            if field.metadata.get('skip', False):
                continue
            dictname = field.metadata.get('dict_name', field.name)
            res[dictname] = getattr(self, field.name)
        return res

    @classmethod
    def deserialize(cls: Type[T], dict_input: Dict[str, Any]) -> T:
        """Nested struct only deserialize one level"""
        kwargs = {}
        for field in cls.__dataclass_fields__.values():  # type: ignore
            dictname = field.metadata.get('dict_name', field.name)
            potential_val = dict_input.get(dictname)
            if potential_val is not None:
                # unions have this attribute
                # Assume its a normal type
                possible_types = getattr(field.type, '__args__', [field.type])
                if isinstance(potential_val, possible_types):
                    kwargs[field.name] = potential_val
                    continue

                # if potential_val is str, and have a from_str constructor:
                metadata = field.metadata
                if isinstance(potential_val, str):
                    if 'from_str' in metadata:
                        from_str = metadata['from_str']
                        kwargs[field.name] = from_str(potential_val)
                        continue

                    if possible_types[0] == datetime.datetime:
                        kwargs[field.name] = parse_iso_datetime(potential_val)
                        continue

                    if possible_types[0] == datetime.date:
                        kwargs[field.name] = parse_iso_date(potential_val)
                        continue

                # try use the first type, this is last resort
                kwargs[field.name] = possible_types[0](potential_val)
        return cls(**kwargs)

    def to_json(self) -> str:
        return json_dumps(self.serialize())


class TypedSerializableMixin(object):
    _fields = ()  # type: Tuple
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
    _name = ()  # type: Tuple

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


def mkgetter(obj: Any) -> Callable:
    if hasattr(obj, 'get'):
        return obj.get
    return obj.__getattribute__


def decode_str(strobj: bytes) -> str:
    try:
        # current clientside uses latin1 because that is the
        # default for apache's httpclient
        content = strobj.decode('latin1')
        # latin1 never fails, so make sure that its printable i.e. currect
        if all(unicodedata.category(c) != 'Cc' for c in content):
            return content
    except UnicodeError:
        pass
    # Assumes utf8 as catchall
    return strobj.decode('utf-8')


def mksetter(obj: Any) -> Callable:
    if hasattr(obj, 'get'):
        return obj.__setitem__
    return obj.__setattr__


def fieldcopy(src, dest, fields):
    srcgetter = mkgetter(src)
    destsetter = mksetter(dest)
    for f in fields:
        try:
            value = srcgetter(f)
            if isinstance(value, bytes):
                value = decode_str(value)
            destsetter(f, value)
        except:
            pass