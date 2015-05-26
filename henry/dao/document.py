import datetime
import os

from henry.layer2.documents import Status
from henry.helpers.serialization import DbMixin, SerializableMixin
from henry.layer1.schema import NNota
from henry.helpers.serialization import json_loads
from henry.layer2.client import Client
from henry.layer2.productos import Transaction
from henry.dao.item_set import MetaItemSet


class InvMetadata(SerializableMixin, DbMixin):
    _db_class = NNota
    _excluded_vars = ('client',)
    _db_attr = {
        'uid': 'id',
        'codigo': 'codigo',
        'client': 'client',
        'user': 'user',
        'timestamp': 'timestamp',
        'status': 'status',
        'total': 'total',
        'tax': 'tax',
        'subtotal': 'subtotal',
        'discount': 'discount',
        'bodega_id': 'bodega',
        'almacen_id': 'almacen_id'}

    _name = _db_attr.keys()

    @classmethod
    def deserialize(cls, the_dict):
        x = cls().merge_from(the_dict)
        client = Client.deserialize(the_dict['client'])
        x.client = client
        return x



class Invoice(MetaItemSet):
    _metadata_cls = InvMetadata

    def items_to_transaction(self):
        reason = 'factura: id={} codigo={}'.format(
            self.meta.uid, self.meta.codigo)
        for prod, cant in self.items:
            yield Transaction(self.meta.bodega, prod.codigo, -cant, prod.nombre,
                              reason, self.meta.timestamp)

    def validate(self):
        if getattr(self.meta, 'codigo', None) is None:
            raise ValueError('codigo cannot be None to save an invoice')

    @property
    def filepath_format(self):
        return os.path.join(
            self.meta.timestamp.date().isoformat(), self.meta.codigo)



class DocumentApi:

    def __init__(self, sessionmanager, filemanager, object_cls):
        self.db_session = sessionmanager
        self.filemanager = filemanager

        self.cls = object_cls
        self.metadata_cls = object_cls._metadata_cls
        self.db_class = self.metadata_cls._db_class


    def get_doc(self, uid):
        """
        uid id of the tranfer to fetch,
        returns Transferencia object
        """
        session = self.db_session.session
        db_instance = session.query(self.db_class).filter_by(id=uid).first()
        content = json_loads(self.filemanager.get_file(db_instance.item_location))
        doc = self.cls.deserialize(content)
        #  sometimes db has more updated information
        meta_from_db = self.metadata_cls.from_db_instance(db_instance)
        doc.meta.merge_from(meta_from_db)
        return doc

    def save(self, doc):
        meta = doc.meta
        if not hasattr(meta, 'timestamp'):
            meta.timestamp = datetime.datetime.now()

        doc.validate()
        filepath = doc.filepath_format
        session = self.db_session.session
        db_entry = meta.db_instance()
        db_entry.items_location = filepath
        session.add(db_entry)
        session.flush()  # flush to get the autoincrement id
        meta.status = Status.NEW
        doc.meta.uid = db_entry.id

        self.filemanager.put_file(filepath, doc.to_json())
        return doc

