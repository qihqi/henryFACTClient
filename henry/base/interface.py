from typing import TypeVar, Generic, Type, Any, Dict
from sqlalchemy.sql.schema import Column
from sqlalchemy.util._collections import OrderedProperties
from henry.schema.base import Base


DBType = TypeVar('DBType', bound=Base)  # this is one of the sqlalchemy classes
SelfType = TypeVar('SelfType', bound='DBObjectInterface')
class DBObjectInterface(Generic[DBType]):
    """Interface for objects that knows how to convert into a db object.

    The db object can the be used with DBApiGeneric to save and store stuff.
    """

    # class of the db object
    db_class: Type[DBType]

    def db_instance(self) -> DBType:
        pass

    @classmethod
    def from_db_instance(cls: Type[SelfType], dbins: DBType) -> SelfType:
        pass


T = TypeVar('T', bound='SerializableInterface')
class SerializableInterface(object):

    def merge_from(self: T, obj: Any) -> T:
        pass

    def serialize(self) -> Dict[str, Any]:
        """Nested struct only deserialize one level"""
        pass

    @classmethod
    def deserialize(cls: Type[T], dict_input: Dict[str, Any]):
        pass

    def to_json(self) -> str:
        pass
