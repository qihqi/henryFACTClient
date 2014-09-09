import os
import json
import itertools
import uuid
import datetime
from itertools import imap
from collections import defaultdict

from sqlalchemy.sql import bindparam
from henry.layer1.schema import NProducto, NContenido, NNota, NBodega
from henry.helpers.serialization import SerializableMixin, decode
from henry.layer2.documents import DocumentApi
from henry.layer2.productos import Transaction


class InvMetadata(SerializableMixin):
    _name = (
        'uid',
        'codigo',
        'client',
        'user',
        'timestamp',
        'status',
        'total',
        'tax',
        'subtotal',
        'discount',
        'bodega',
        'almacen')

    def __init__(self, **kwargs):
        if 'timestamp' not in kwargs:
            kwargs['timestamp'] = None
        self.__dict__ = kwargs


class Invoice(SerializableMixin):
    _name = ('meta', 'items')

    def __init__(self, meta=None, items=None):
        self.meta = meta
        # list of tuples of (prod_id, cant, name, price)
        self.items = items

    @classmethod
    def deserialize(cls, dict_input):
        meta = InvMetadata.deserialize(dict_input['meta'])
        items = dict_input['items']
        return cls(meta, items)


class InvApiDB(DocumentApi):
    _query_string = (
        NNota.id.label('uid'),
        NNota.status,
        NNota.items_location,
        NNota.codigo,
        )
    _db_class = NNota
    _datatype = Invoice

    def _validate_metadata(self, meta):
        if meta.bodega is None:
            raise ValueError('No tiene bodega')
        if meta.almacen is None:
            raise ValueError('No tiene almacen')

    @classmethod
    def _db_instance(cls, meta, filepath):
        return NNota(
            codigo=meta.codigo,
            client=meta.client,
            user=meta.user,
            timestamp=meta.timestamp,
            status=meta.status,
            total=meta.total,
            tax=meta.tax,
            subtotal=meta.subtotal,
            discount=meta.discount,
            bodega=meta.bodega,
            almacen=meta.almacen,
            items_location=filepath
            )

    @classmethod
    def _items_to_transactions(cls, doc):
        reason = 'factura: id={} codigo={}'.format(doc.meta.uid, doc.meta.codigo)
        for i in doc.items:
            prod_id, prod, cant, price = i
            yield Transaction(doc.meta.bodega, prod_id, -cant, prod, reason)

    def create_document_from_request(self, req):
        inv = Invoice(req.meta)
        items = []
        for i in req.items:
            p = self.prod_api.get_producto(i[0])
            if p is None:
                raise ValueError('producto {} no existe'.format(prod_id))
            if i[1] < 0:
                raise ValueError('Cantidad de producto {} es negativo'.format(prod_id))
            if i[1] > 0:
                items.append(i)
        inv.items = items
        return inv

    def set_codigo(self, uid, codigo):
        self.db_session.query(NNota).filter_by(id=uid).update({'codigo' : codigo})




