import logging
import datetime
import os
from decimal import Decimal
from typing import Type, List

from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from henry.base.fileservice import FileService
from henry.base.session_manager import SessionManager
from henry.base.dbapi import DBApiGeneric, SerializableDB

from henry.base.serialization import SerializableMixin
from henry.base.serialization import json_loads
from henry.invoice.coreschema import NPedidoTemporal
from henry.product.dao import PriceList, InvMovementType, InventoryApi, InventoryMovement

from typing import Iterable, Optional, TypeVar, Generic


class Status(object):
    NEW = 'NUEVO'
    COMITTED = 'POSTEADO'
    DELETED = 'ELIMINADO'

    names = (NEW,
             COMITTED,
             DELETED)


class Item(SerializableMixin):
    prod: PriceList
    cant: Decimal
    _name = ('prod', 'cant')

    def __init__(self, prod=None, cant=None):
        self.prod = prod
        self.cant = cant

    @classmethod
    def deserialize(cls, the_dict):
        prod = PriceList.deserialize(the_dict['prod'])
        cant = Decimal(the_dict['cant'])
        return cls(prod, cant)


T = TypeVar('T', bound=SerializableDB)
SelfType = TypeVar('SelfType', bound='MetaItemSet')
class MetaItemSet(SerializableMixin, Generic[T]):
    _name = ('meta', 'items')
    _metadata_cls: Type[T]  # _metadata class must have a field item_location
    meta: Optional[T]
    items: List[Item]

    def __init__(self, meta: Optional[T] = None,
                 items: Iterable[Item] = []):
        self.meta = meta
        self.items = list(items)

    def items_to_transaction(self, dbapi) -> Iterable[InventoryMovement]:
        raise NotImplementedError()

    @classmethod
    def deserialize(cls: Type[SelfType], the_dict) -> SelfType:
        x = cls()
        print('MetaItemset.deserialzie', the_dict)
        x.meta = cls._metadata_cls.deserialize(the_dict['meta'])
        x.items = list(map(Item.deserialize, the_dict['items']))
        return x

    def validate(self):
        raise NotImplementedError

    @property
    def filepath_format(self) -> str:
        raise NotImplementedError


Doc = TypeVar('Doc', bound=MetaItemSet)
class DocumentApi(object):
    def __init__(self, sessionmanager: SessionManager,
                 filemanager: FileService,
                 transaction: InventoryApi,
                 object_cls: Type[Doc]):
        self.db_session = sessionmanager
        self.dbapi = DBApiGeneric(sessionmanager)
        self.filemanager = filemanager
        self.transaction = transaction

        self.cls = object_cls
        self.metadata_cls = object_cls._metadata_cls
        self.db_class = self.metadata_cls.db_class

    def get_doc(self, uid) -> Optional[Doc]:
        session = self.db_session.session
        pkey_col = inspect(self.db_class).primary_key[0]
        db_instance = session.query(self.db_class).filter(pkey_col == uid).first()
        meta = self.dbapi.get(uid, self.metadata_cls)
        if meta is None:
            print('cannot find document in table ', self.db_class.__tablename__, end=' ')
            print(' with id ', uid)
            return None
        doc = self.get_doc_from_file(meta.items_location)  # type: ignore
        if doc is not None:
            doc.meta.status = meta.status  # type: ignore
        return doc

    def get_doc_from_file(self, filename: str) -> Optional[Doc]:
        file_content = self.filemanager.get_file(filename)
        if file_content is None:
            print('could not find file at ', filename)
            return None
        content = json_loads(file_content)
        doc = self.cls.deserialize(content)
        return doc

    def save(self, doc: Doc):
        meta = doc.meta
        assert meta is not None
        if not hasattr(meta, 'timestamp'):
            meta.timestamp = datetime.datetime.now()
        if not meta.status:
            meta.status = Status.NEW
        doc.validate()
        meta.items_location = doc.filepath_format
        self.dbapi.create(meta)
        self.filemanager.put_file(meta.items_location, doc.to_json())
        return doc

    def commit(self, doc: Doc):
        meta = doc.meta
        if meta.status and meta.status != Status.NEW:  # type: ignore
            logging.info('attempt to commit doc {} in wrong status'.format(doc.meta.uid))  # type: ignore
            return None
        if self._set_status_and_update_prod_count(
                doc, Status.COMITTED, inverse_transaction=False):
            return doc
        return None

    def delete(self, doc: Doc):
        assert doc.meta is not None
        if doc.meta.status == Status.COMITTED:
            if self._set_status_and_update_prod_count(
                    doc, Status.DELETED, inverse_transaction=True):
                return doc
            return None
        elif doc.meta.status == Status.NEW:
            count = self.dbapi.update(doc.meta, {'status': Status.DELETED})
            if count > 0:
                return doc
        logging.info('attempt to delete doc {} which is not committed'.format(
            doc.meta.uid))  # type: ignore
        return None

    def _set_status_and_update_prod_count(
            self, doc: Doc, new_status: str, inverse_transaction: bool) -> bool:
        session = self.db_session.session
        now = datetime.datetime.now()
        assert doc.meta is not None
        try:
            items = list(doc.items_to_transaction(self.dbapi))
            for i in items:
                if inverse_transaction:
                    i.type = InvMovementType.delete_type(i.type)
                    i.inverse()
                i.timestamp = now
            self.transaction.bulk_save(items)
            self.dbapi.update(doc.meta, {'status': new_status})
            session.commit()
            doc.meta.status = new_status
            return True
        except SQLAlchemyError:
            import traceback
            traceback.print_exc()
            session.rollback()
            return False

    def search_metadata_by_date_range(self, start, end, status=None, other_filters=None):
        session = self.db_session.session
        query = session.query(self.db_class).filter(
            self.db_class.timestamp >= start).filter(
            self.db_class.timestamp <= end)
        if status is not None:
            query = query.filter_by(status=status)
        if other_filters:
            query = query.filter_by(**other_filters)
        for r in query:
            meta = self.metadata_cls.from_db_instance(r)
            meta.items_location = r.items_location
            yield meta


class PedidoApi(object):
    def __init__(self, sessionmanager, filemanager):
        self.session = sessionmanager
        self.filemanager = filemanager

    def save(self, raw_content, user=None, status='pedido'):
        session = self.session.session
        timestamp = datetime.datetime.now()
        pedido = NPedidoTemporal(
            user=user,
            timestamp=timestamp,
            status=status)
        session.add(pedido)
        session.flush()
        codigo = str(pedido.id)
        filename = os.path.join(timestamp.date().isoformat(), codigo)
        filename = self.filemanager.put_file(filename, raw_content)
        return codigo, filename

    def get_doc(self, uid):
        current_date = datetime.date.today()
        look_back = 7
        uid = str(uid)
        for i in range(look_back):
            cur_date = current_date - datetime.timedelta(days=i)
            filename = os.path.join(cur_date.isoformat(), uid)
            f = self.filemanager.get_file(filename)
            if f is not None:
                return f
        logging.info('Could not find pedido within {} days of lookback'.format(look_back))
        return None
