import os
import json
import uuid
import datetime
from itertools import imap
from collections import defaultdict

from sqlalchemy.exc import SQLAlchemyError


class Status:
    NEW = 'NUEVO'
    COMITTED = 'POSTEADO'
    DELETED = 'ELIMINADO'

    names = (NEW,
             COMITTED,
             DELETED)


class DocumentException(Exception):
    pass


class DocumentCreationRequest(object):
    """
    this class has 2 fields:
        meta is an instance of Metadata
        items is a dict with (prod_id -> cant)
    """
    def __init__(self, meta=None):
        self.meta = meta
        self.items = defaultdict(int)

    def add(self, prod_id, cant):
        self.items[prod_id] += cant


class DocumentApi(object):
    '''
    A document have 2 parts, one for metadata, one for content
    content will be an iterable of tuples, detailing at least
    product id and quatity.
    An Invoice, An Ingress are both documents.

    Metadata could be very different, the only common things is that its
    saved in one row in the database, and have one field called uid for id,
    and another
    items_location as a logical location for where the content is stored.

    API:
     * get_doc
     * commit
     * delete
    '''

    def __init__(self, sessionmanager, filemanager, prod_api):
        self.db_session = sessionmanager
        self.filemanager = filemanager
        self.prod_api = prod_api

    def _item_generator(self, meta, prod, cantidad):
        pass

    def _items_to_transactions(self, doc):
        pass

    def get_doc(self, uid):
        """
        uid id of the tranfer to fetch,
        returns Transferencia object
        """
        session = self.db_session.session
        meta = session.query(*self._query_string).filter_by(id=uid).first()
        return self.get_doc_from_meta(meta)

    def get_doc_from_meta(self, meta):
        if meta is None:
            return None
        parsed = json.loads(self.filemanager.get_file(meta.items_location))
        t = self._datatype.deserialize(parsed)
        t.meta.merge_from(meta)
        return t

    def save(self, request):
        request.meta.timestamp = (request.meta.timestamp
                                  or datetime.datetime.now())
        doc = self.create_document_from_request(request)

        session = self.db_session.session
        meta = doc.meta
        meta.status = Status.NEW
        filepath = os.path.join(
            meta.timestamp.date().isoformat(), uuid.uuid1().hex)
        db_entry = self._db_instance(meta, filepath)
        session.add(db_entry)
        session.flush()  # flush to get the autoincrement id
        doc.meta.uid = db_entry.id
        self.filemanager.put_file(filepath, doc.to_json())
        return doc

    def commit(self, uid):
        doc = self.get_doc(uid)
        if doc is None:
            return None
        meta = doc.meta
        if meta.status and meta.status != Status.NEW:
            return None
        if self._set_status_and_update_prod_count(
                doc, Status.COMITTED, inverse_transaction=False):
            return doc
        return None

    def delete(self, uid):
        doc = self.get_doc(uid)
        if doc.meta.status != Status.COMITTED:
            return None
        if self._set_status_and_update_prod_count(
                doc, Status.DELETED, inverse_transaction=True):
            return doc
        return None

    def _set_status_and_update_prod_count(
            self, doc, new_status, inverse_transaction):
        session = self.db_session.session
        try:
            items = self._items_to_transactions(doc)
            if inverse_transaction:
                items = imap(lambda i: i.inverse(), items)
            self.prod_api.execute_transactions(items)
            session.query(self._db_class).filter_by(
                id=doc.meta.uid).update({'status': new_status})
            session.commit()
            doc.meta.status = new_status
            return True
        except SQLAlchemyError:
            import traceback
            traceback.print_exc()
            session.rollback()
            return False
