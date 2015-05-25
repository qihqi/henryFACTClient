import datetime
import os

from henry.layer2.documents import Status
from henry.helpers.serialization import DbMixin, SerializableMixin
from henry.layer1.schema import NNota
from henry.helpers.serialization import json_loads
from henry.layer2.client import Client
from henry.dao.item_set import Item, MetaItemSet


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

class InvoiceApi:

    def __init__(self, sessionmanager, filemanager):
        self.db_session = sessionmanager
        self.filemanager = filemanager

    def get_doc(self, uid):
        """
        uid id of the tranfer to fetch,
        returns Transferencia object
        """
        session = self.db_session.session
        db_instance = session.query(InvMetadata._db_class).filter_by(id=uid).first()
        content = json_loads(self.filemanager.get_file(db_instance.item_location))
        meta = InvMetadata()
        meta.merge_from(content['meta'])
        meta.client = Client.deserialize(meta.client)
        meta.merge_from(InvMetadata.from_db_instance(db_instance))
        items = map(Item.deserialize, content['items'])
        return MetaItemSet(meta, items)

    def save(self, inv):
        meta = inv.meta
        if not hasattr(meta, 'timestamp'):
            meta.timestamp = datetime.datetime.now()
        if getattr(meta, 'codigo', None) is None:
            raise ValueError('codigo cannot be None to save an invoice')
        filepath = os.path.join(
            self.filemanager.root,
            meta.timestamp.date().isoformat(), meta.codigo)

        session = self.db_session.session
        db_entry = meta.db_instance()
        db_entry.item_location = filepath
        session.add(db_entry)
        session.flush()  # flush to get the autoincrement id
        meta.status = Status.NEW
        inv.meta.uid = db_entry.id

        self.filemanager.put_file(filepath, inv.to_json())
        return inv

    def items_to_transactions(cls, doc):
        reason = 'factura: id={} codigo={}'.format(
            doc.meta.uid, doc.meta.codigo)
        for prod, cant in doc.items:
            yield Transaction(doc.meta.bodega, prod.codigo, -cant, prod.nombre, 
                              ref=reason, doc.meta.timestamp)
