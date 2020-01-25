from sqlalchemy.inspection import inspect

from typing import (Type, TypeVar, Generic,
                    Mapping, Optional, List)
from sqlalchemy.orm.session import Session

from henry.base.serialization import fieldcopy
from henry.base.serialization import SerializableData
from henry.schema.base import Base
from henry.base.session_manager import SessionManager

DBType = TypeVar('DBType', bound=Base)  # this is one of the sqlalchemy classes
SelfType = TypeVar('SelfType', bound='SerializableDB')
class SerializableDB(SerializableData, Generic[DBType]):
    """Interface for objects that knows how to convert into a db object.

    The db object can the be used with DBApiGeneric to save and store stuff.
    """

    # class of the db object
    db_class: Type[DBType]

    def db_instance(self) -> DBType:
        columns = inspect(self.db_class).columns
        result = self.db_class()
        fieldcopy(self, result, columns.keys())
        return result

    @classmethod
    def from_db_instance(cls: Type[SelfType], db_instance) -> SelfType:
        columns = inspect(cls.db_class).columns
        y = cls()
        fieldcopy(db_instance, y, columns.keys())
        return y


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


T = TypeVar('T', bound='SerializableDB')
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

    def create(self, obj: SerializableDB):
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

    def update(self, obj: SerializableDB, content_dict: Mapping) -> int:
        pkey_col = inspect(obj.db_class).primary_key[0]
        pkey = getattr(obj, pkey_col.name)
        count = self.sm.session.query(obj.db_class).filter(
            pkey_col == pkey).update(
            content_dict)
        for x, y in list(content_dict.items()):
            setattr(obj, x, y)
        return count

    def update_full(self, obj: SerializableDB) -> int:
        columns = inspect(obj.db_class).columns
        pkey_col = inspect(obj.db_class).primary_key[0]
        values = {col: getattr(obj, col)
                  for col in list(columns.keys())
                  if col != pkey_col.name}
        return self.update(obj, values)

    def delete(self, obj: SerializableDB) -> int:
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
