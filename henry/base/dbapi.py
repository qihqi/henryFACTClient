import abc

from sqlalchemy.inspection import inspect

from typing import (Callable, Any, Type, TypeVar, Generic,
                    Dict, Mapping, Optional, List, Dict, Set, Iterable)
from sqlalchemy.orm.session import Session

from henry.base.interface import DBObjectInterface, DBType
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


class P:

    columns: Dict

    def db_instance(self):
        result = self.db_class()
        fieldcopy(self, result, self.columns.keys())
        return result

    @classmethod
    def from_db_instance(cls, db_instance):
        y = cls()
        fieldcopy(db_instance, y, cls.columns.keys())
        return y

    def merge_from(self, obj):
        fieldcopy(obj, self, self.columns.keys())
        return self

    def serialize(self):
        result = {}
        fieldcopy(self, result, self.columns.keys())
        return result

    @classmethod
    def deserialize(cls, dict_input):
        result = cls().merge_from(dict_input)
        return result


# Use as decorator
def dbmix(database_class: Type[DBType]):
    columns = inspect(database_class).columns
    def wrap(clazz):
        clazz.db_class = database_class
        clazz.columns = columns

        def db_instance(self):
            result = self.db_class()
            fieldcopy(self, result, columns.keys())
            return result
        clazz.db_instance = db_instance

        @classmethod
        def from_db_instance(cls, db_instance):
            y = cls()
            fieldcopy(db_instance, y, columns.keys())
            return y
        clazz.from_db_instance = from_db_instance

        def merge_from(self, obj):
            fieldcopy(obj, self, columns.keys())
            return self
        clazz.merge_from = merge_from

        def serialize(self):
            result = {}
            fieldcopy(self, result, columns.keys())
            return result
      #  clazz.serialize = serialize

        @classmethod
        def deserialize(cls, dict_input):
            result = cls().merge_from(dict_input)
            return result
      #  clazz.deserialize = deserialize

        return clazz
    return wrap


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


T = TypeVar('T', bound='DBObjectInterface')
class DBApiGeneric(object):

    # db_class = database_class  # type: Type[DBType]
    # _columns = inspect(database_class).columns
    # pkey = inspect(database_class).primary_key[0]
    def __init__(self, sessionmanager: SessionManager):
        self.sm = sessionmanager

    @property
    def session(self) -> SessionManager:
        return self.sm

    @property
    def db_session(self) -> Session:
        return self.sm.session

    def create(self, obj: DBObjectInterface):
        pkey_col = inspect(obj.db_class).primary_key[0]
        dbobj = obj.db_instance()
        self.sm.session.add(dbobj)
        self.sm.session.flush()
        pkey = pkey_col.name
        pkeyval = getattr(dbobj, pkey)
        setattr(obj, pkey, pkeyval)
        return pkeyval

    def get(self, pkey, objclass: Type[T]) -> Optional[T]:
        pkey_col = inspect(objclass.db_class).primary_key[0]
        db_instance = self.sm.session.query(objclass.db_class).filter(
            pkey_col == pkey).first()
        if db_instance is None:
            return None
        return objclass.from_db_instance(db_instance)

    def update(self, obj: DBObjectInterface, content_dict: Mapping) -> int:
        pkey_col = inspect(obj.db_class).primary_key[0]
        pkey = getattr(obj, pkey_col.name)
        count = self.sm.session.query(obj.db_class).filter(
            pkey_col == pkey).update(
            content_dict)
        for x, y in list(content_dict.items()):
            setattr(obj, x, y)
        return count

    def update_full(self, obj: DBObjectInterface) -> int:
        columns = inspect(obj.db_class).columns
        pkey_col = inspect(obj.db_class).primary_key[0]
        values = {col: getattr(obj, col)
                  for col in list(columns.keys())
                  if col != pkey_col.name}
        return self.update(obj, values)

    def delete(self, obj: DBObjectInterface) -> int:
        pkey_col = inspect(obj.db_class).primary_key[0]
        pkey = getattr(obj, pkey_col.name)
        count = self.sm.session.query(obj.db_class).filter(
            pkey_col == pkey).delete()
        return count

    def getone(self, objclass: Type[T], **kwargs) -> Optional[T]:
        result = self.search(objclass, **kwargs)
        if not result:
            return None
        return result[0]

    def search(
        self, objclass: Type[T], **kwargs) -> List[T]:
        query = self.sm.session.query(objclass.db_class)
        columns = inspect(objclass.db_class).columns
        for key, value in list(kwargs.items()):
            mode = None
            if '-' in key:
                key, mode = key.split('-')
            col = columns[key]
            f = col == value
            if mode == 'prefix':
                f = col.startswith(value)
            if mode == 'lte':
                f = col <= value
            if mode == 'gte':
                f = col >= value
            query = query.filter(f)
        return list(map(objclass.from_db_instance, iter(query)))
