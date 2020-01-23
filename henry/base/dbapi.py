import abc

from sqlalchemy.inspection import inspect

from typing import Callable, Any, Type, TypeVar, Generic, Dict, Mapping, Optional, List
from sqlalchemy.orm.session import Session
from sqlalchemy.sql.schema import Column
from sqlalchemy.util._collections import OrderedProperties
from henry.base.session_manager import SessionManager


def decode_str(strobj: bytes) -> str:
    try:
        return strobj.decode('utf-8')
    except:
        return strobj.decode('latin1')


def mkgetter(obj: Any) -> Callable:
    if hasattr(obj, 'get'):
        return obj.get
    return obj.__getattribute__


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

DBType = TypeVar('DBType')
MappedType = TypeVar('MappedType')


class DBObjectInterface(abc.ABC, Generic[DBType]):

    pkey: Column
    _columns: OrderedProperties
    db_class: Type[DBType]

    @abc.abstractmethod
    def db_instance(self) -> DBType:
        pass

    @abc.abstractmethod
    def serialize(self) -> Dict:
        pass

    @classmethod
    @abc.abstractmethod
    def deserialize(cls, content: Dict) -> MappedType:
        pass

    @classmethod
    @abc.abstractmethod
    def from_db_instance(cls, dbins: DBType) -> MappedType:
        pass



# A method that converts a class of SQLAlchemy model into
# a serializeble object
# APIs:
#     .db_instance() returns an object of the given class with the same data
#     .serialize() returns an dict with same data
#     Class.from_db_instance, and Class.deserialize do the opposite
def dbmix(database_class: Type[DBType], override_name=()) -> Type[DBObjectInterface[DBType]]:
    class DataObjectMixin(DBObjectInterface[DBType]):
        db_class = database_class  # type: Type[DBType]
        _columns = inspect(database_class).columns
        pkey = inspect(database_class).primary_key[0]

        def __init__(self, **kwargs):
            self.merge_from(kwargs)

        def db_instance(self):
            result = self.db_class()
            fieldcopy(self, result, list(self._columns.keys()))
            return result

        @classmethod
        def from_db_instance(cls, db_instance):
            y = cls()
            fieldcopy(db_instance, y, list(cls._columns.keys()))
            return y

        def merge_from(self, obj):
            fieldcopy(obj, self, list(self._columns.keys()))
            return self

        def serialize(self):
            return self._serialize_helper(self, list(self._columns.keys()))

        @classmethod
        def deserialize(cls, dict_input):
            result = cls().merge_from(dict_input)
            for x, y in override_name:
                original = dict_input.get(y, None)
                setattr(result, x, original)
            return result

        @classmethod
        def _serialize_helper(cls, obj, names):
            result = {}
            fieldcopy(obj, result, names)
            for x, y in override_name:
                original = result[x]
                result[y] = original
                del result[x]
            return result

    return DataObjectMixin


class DBApi(object):

    def __init__(self, sessionmanager, objclass):
        self.sm = sessionmanager
        self.objclass = objclass
        self.api = DBApiGeneric(sessionmanager)

    def create(self, obj):
        return self.api.create(obj)

    def get(self, pkey):
        return self.api.get(pkey, self.objclass)

    def update(self, pkey, content_dict):
        obj = self.objclass()
        setattr(obj, self.objclass.pkey.name, pkey)
        return self.api.update(obj, content_dict)

    def delete(self, pkey):
        obj = self.objclass()
        setattr(obj, self.objclass.pkey.name, pkey)
        return self.api.delete(obj)

    def getone(self, **kwargs):
        return self.api.getone(self.objclass, **kwargs)

    def search(self, **kwargs):
        return self.api.search(self.objclass, **kwargs)


class DBApiGeneric(object):

    def __init__(self, sessionmanager: SessionManager):
        self.sm = sessionmanager

    @property
    def session(self) -> SessionManager:
        return self.sm

    @property
    def db_session(self) -> Session:
        return self.sm.session

    def create(self, obj: DBObjectInterface):
        dbobj = obj.db_instance()
        self.sm.session.add(dbobj)
        self.sm.session.flush()
        pkey = obj.pkey.name
        pkeyval = getattr(dbobj, pkey)
        setattr(obj, pkey, pkeyval)
        return pkeyval

    def get(self, pkey, objclass: Type[DBObjectInterface[DBType]]
            ) -> Optional[DBObjectInterface[DBType]]:
        db_instance = self.sm.session.query(objclass.db_class).filter(
            objclass.pkey == pkey).first()
        if db_instance is None:
            return None
        return objclass.from_db_instance(db_instance)

    def update(self, obj: DBObjectInterface, content_dict: Mapping) -> int:
        pkey = getattr(obj, obj.pkey.name)
        count = self.sm.session.query(obj.db_class).filter(
            obj.pkey == pkey).update(
            content_dict)
        for x, y in list(content_dict.items()):
            setattr(obj, x, y)
        return count

    def update_full(self, obj: DBObjectInterface) -> int:
        values = {col: getattr(obj, col)
                  for col in list(obj._columns.keys())
                  if col != obj.pkey.name}
        return self.update(obj, values)

    def delete(self, obj: DBObjectInterface) -> int:
        pkey = getattr(obj, obj.pkey.name)
        count = self.sm.session.query(obj.db_class).filter(
            obj.pkey == pkey).delete()
        return count

    def getone(
            self, objclass: Type[DBObjectInterface[DBType]], **kwargs
    ) -> Optional[DBObjectInterface[DBType]]:
        result = self.search(objclass, **kwargs)
        if not result:
            return None
        return result[0]

    def search(
        self, objclass: Type[DBObjectInterface[DBType]], **kwargs
    ) -> List[DBObjectInterface[DBType]]:
        query = self.sm.session.query(objclass.db_class)
        for key, value in list(kwargs.items()):
            mode = None
            if '-' in key:
                key, mode = key.split('-')
            col = objclass._columns[key]
            f = col == value
            if mode == 'prefix':
                f = col.startswith(value)
            if mode == 'lte':
                f = col <= value
            if mode == 'gte':
                f = col >= value
            query = query.filter(f)
        return list(map(objclass.from_db_instance, iter(query)))
