import logging
import datetime
import os
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError

from henry.base.serialization import SerializableMixin
from henry.base.serialization import json_loads
from henry.schema.inv import NPedidoTemporal
from .coredao import PriceList


class Status:
    NEW = 'NUEVO'
    COMITTED = 'POSTEADO'
    DELETED = 'ELIMINADO'

    names = (NEW,
             COMITTED,
             DELETED)


class Item(SerializableMixin):
    _name = ('prod', 'cant')

    def __init__(self, prod=None, cant=None):
        self.prod = prod
        self.cant = cant

    @classmethod
    def deserialize(cls, the_dict):
        prod = PriceList.deserialize(the_dict['prod'])
        cant = Decimal(the_dict['cant'])
        return cls(prod, cant)


class MetaItemSet(SerializableMixin):
    _name = ('meta', 'items')
    _metadata_cls = None

    def __init__(self, meta=None, items=None):
        self.meta = meta
        self.items = list(items) if items else []

    def items_to_transaction(self):
        raise NotImplementedError()

    @classmethod
    def deserialize(cls, the_dict):
        x = cls()
        x.meta = cls._metadata_cls.deserialize(the_dict['meta'])
        x.items = map(Item.deserialize, the_dict['items'])
        return x


class DocumentApi:
    def __init__(self, sessionmanager, filemanager, transaction, object_cls):
        self.db_session = sessionmanager
        self.filemanager = filemanager
        self.transaction = transaction

        self.cls = object_cls
        self.metadata_cls = object_cls._metadata_cls
        self.db_class = self.metadata_cls._db_class

    def get_doc(self, uid):
        session = self.db_session.session
        db_instance = session.query(self.db_class).filter_by(id=uid).first()
        if db_instance is None:
            print 'cannot find document in table ', self.db_class.__tablename__,
            print ' with id ', uid
            return None
        doc = self.get_doc_from_file(db_instance.items_location)
        doc.meta.status = db_instance.status
        return doc

    def get_doc_from_file(self, filename):
        file_content = self.filemanager.get_file(filename)
        if file_content is None:
            print 'could not find file at ', filename
            return None
        content = json_loads(file_content)
        doc = self.cls.deserialize(content)
        return doc

    def save(self, doc):
        meta = doc.meta
        if not hasattr(meta, 'timestamp'):
            meta.timestamp = datetime.datetime.now()
        if not meta.status:
            meta.status = Status.NEW
        doc.validate()
        filepath = doc.filepath_format
        session = self.db_session.session
        db_entry = meta.db_instance()
        db_entry.items_location = filepath
        session.add(db_entry)
        session.flush()  # flush to get the autoincrement id
        doc.meta.uid = db_entry.id

        self.filemanager.put_file(filepath, doc.to_json())
        return doc

    def commit(self, doc):
        meta = doc.meta
        if meta.status and meta.status != Status.NEW:
            logging.info('attempt to commit doc {} in wrong status'.format(doc.meta.uid))
            return None
        if self._set_status_and_update_prod_count(
                doc, Status.COMITTED, inverse_transaction=False):
            return doc
        return None

    def delete(self, doc):
        if doc.meta.status == Status.COMITTED:
            if self._set_status_and_update_prod_count(
                    doc, Status.DELETED, inverse_transaction=True):
                return doc
            return None
        elif doc.meta.status == Status.NEW:
            count = self.db_session.session.query(self.db_class).filter_by(
                id=doc.meta.uid).update({'status': Status.DELETED})
            if count > 0:
                doc.meta.status = Status.DELETED
                return doc
        logging.info('attempt to delete doc {} which is not committed'.format(doc.meta.uid))
        return None

    def _set_status_and_update_prod_count(
            self, doc, new_status, inverse_transaction):
        session = self.db_session.session
        try:
            items = list(doc.items_to_transaction())
            for i in items:
                i.ref = '{}: {}'.format(new_status, i.ref)
                if inverse_transaction:
                    i.inverse()
            self.transaction.bulk_save(items)
            session.query(self.db_class).filter_by(
                id=doc.meta.uid).update({'status': new_status})
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


class PedidoApi:
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
