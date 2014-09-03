import os
import json
import itertools
import uuid
import datetime
from itertools import imap
from collections import defaultdict

from sqlalchemy.sql import bindparam
from henry.layer1.schema import NProducto, NContenido, NTransferencia, NBodega
from henry.helpers.serialization import SerializableMixin, decode

class TransType:
    INGRESS = 'INGRESO'
    TRANSFER= 'TRANSFER'
    REPACKAGE = 'REEMPAQUE'
    EXTERNAL = 'EXTERNA'

    names = (INGRESS,
             TRANSFER,
             REPACKAGE,
             EXTERNAL)


class Status:
    NEW = 'NUEVO'
    COMITTED = 'POSTEADO'
    DELETED = 'ELIMINADO'

    names = (NEW,
             COMITTED,
             DELETED)



class Product(SerializableMixin):
    _name = ('nombre',
             'codigo',
             'precio1',
             'precio2',
             'threshold',
             'cantidad')

    def __init__(self,
                 codigo=None,
                 nombre=None,
                 precio1=None,
                 precio2=None,
                 threshold=None,
                 cantidad=None,
                 almacen_id=None,
                 bodega_id=None):
        self.codigo = codigo
        self.nombre = nombre
        self.almacen_id = almacen_id
        self.precio1 = precio1
        self.precio2 = precio2
        self.threshold = threshold
        self.bodega_id = bodega_id
        self.cantidad = cantidad


class Transaction(SerializableMixin):
    _name=['bodega_id', 'prod_id', 'delta', 'name', 'ref']

    def __init__(self, bodega_id=None, prod_id=None, delta=None, name=None, ref=None):
        self.bodega_id = bodega_id
        self.prod_id = prod_id
        self.delta = delta
        self.name = name
        self.ref = ref

    def inverse(self):
        self.delta = -self.delta
        return self


class ProductApiDB:

    _PROD_KEYS = (
        NProducto.codigo,
        NProducto.nombre,
    )
    _PROD_PRICE_KEYS = (
        NContenido.bodega_id.label('almacen_id'),
        NContenido.precio.label('precio1'),
        NContenido.precio2,
        NContenido.cant_mayorista.label('threshold')
    )
    _PROD_CANT_KEYS = (
        NContenido.cant.label('cantidad'),
        NContenido.bodega_id,
    )

    def __init__(self, db_session):
        self._prod_name_cache = {}
        self._prod_price_cache = {}
        self.db_session = db_session

    def get_producto(self, prod_id, almacen_id=None, bodega_id=None):
        query_items = list(ProductApiDB._PROD_KEYS)
        filter_items = [NProducto.codigo == prod_id]
        has_alm = almacen_id is not None
        has_bod = bodega_id is not None
        if has_alm or has_bod:
            filter_items.append(NContenido.prod_id == NProducto.codigo)
        if has_alm:
            query_items.extend(ProductApiDB._PROD_PRICE_KEYS)
            filter_items.append(NContenido.bodega_id == almacen_id)
        if has_bod:
            query_items.extend(ProductApiDB._PROD_CANT_KEYS)
            filter_items.append(NContenido.bodega_id == bodega_id)

        item = self.db_session.query(*query_items)
        for f in filter_items:
            item = item.filter(f)
        if item.first() is not None:
            return Product().merge_from(item.first())
        return None

    def search_producto(self, prefix, almacen_id=None, bodega_id=None):
        query_items = list(ProductApiDB._PROD_KEYS)
        filters = [NProducto.nombre.startswith(prefix)]
        if almacen_id is not None:
            query_items.extend(ProductApiDB._PROD_PRICE_KEYS)
            filters.append(NContenido.prod_id == NProducto.codigo)
            filters.append(NContenido.bodega_id == almacen_id)
        if bodega_id is not None:
            query_items.extend(ProductApiDB._PROD_CANT_KEYS)
        result_proxy = self.db_session.query(*query_items)

        for f in filters:
            result_proxy = result_proxy.filter(f)
        for r in result_proxy:
            yield Product().merge_from(r)

    def save(self, prod):
        p = self._construct_db_instance(prod)
        self.db_session.add(p)
        self.db_session.commit()

    def save_batch(self, prods):
        for p in prods:
            x = self._construct_db_instance(p)
            self.db_session.add(x)
        self.db_session.commit()

    def execute_transactions(self, trans):
        rowcount = self.exec_transactions_with_session(self.db_session, trans)
        self.db_session.commit()
        return rowcount

    def exec_transactions_with_session(self, session, trans):
        t = NContenido.__table__.update().where(
                NContenido.prod_id == bindparam('p')).where(
                NContenido.bodega_id == bindparam('b'))
        t = t.values({'cant': NContenido.cant + bindparam('c')})
        substitute = [{'c': x.delta, 'p': x.prod_id, 'b': x.bodega_id} for x in trans]
        print substitute
        result = session.execute(t, substitute)
        return result.rowcount

    def _construct_db_instance(self, prod):
        p = NProducto(
                codigo=prod.codigo,
                nombre=prod.nombre,
                categoria=prod.categoria)
        if prod.almacen_id:
            c = NContenido(
                    bodega_id=prod.almacen_id,
                    precio=prod.precio1,
                    precio2=prod.precio2,
                    )
            p.contenidos.add(c)
        return p

    def get_bodegas(self):
        return self.db_session.query(NBodega);

class Metadata(SerializableMixin):
    _name = (
        'uid',
        'origin',
        'dest',
        'user',
        'trans_type',
        'ref',
        'timestamp',
        'status')

    def __init__(self, trans_type=None,
                       uid=None,
                       origin=None,
                       dest=None,
                       user=None,
                       ref=None,
                       status=None,
                       timestamp=None):
        self.uid = uid
        self.origin = origin
        self.dest = dest
        self.user = user
        self.trans_type = trans_type
        self.ref = ref
        self.timestamp = timestamp
        self.status = status


class TransferCreationRequest:
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


class Transferencia(SerializableMixin):
    _name = ('meta', 'items')

    def __init__(self, meta=None, items=None):
        self.meta = meta
        self.items = items

    @classmethod
    def deserialize(cls, dict_input):
        meta = Metadata.deserialize(dict_input['meta'])
        items = dict_input['items']
        return cls(meta, items)


class TransApiDB:
    _QUERY_KEYS = (
        NTransferencia.id.label('uid'),
        NTransferencia.status,
        NTransferencia.items_location,
        )

    def __init__(self, session, filemanager, prod_api):
        self.db_session = session
        self.filemanager = filemanager
        self.prod_api = prod_api

    def get_doc(self, uid):
        """
        uid id of the tranfer to fetch,
        returns Transferencia object
        """
        meta = self.db_session.query(*TransApiDB._QUERY_KEYS).filter(
                NTransferencia.id == uid).first()
        if meta is None:
            return None
        parsed = json.loads(self.filemanager.get_file(meta.items_location))
        t = Transferencia.deserialize(parsed)
        t.meta.merge_from(meta)
        return t

    def create_transfer_from_request(self, req):
        if req.meta.trans_type is None:
            raise ValueError('Tipo de transferencia no existe')
        if req.meta.dest is None or req.meta.dest == -1:
            raise ValueError('Require bodega de destino')
        if req.meta.trans_type != TransType.INGRESS and req.meta.origin is None:
            raise ValueError('Require origen para transferencia tipo ' + transfer.trans_type)

        t = Transferencia(meta=req.meta)
        t.meta.status = Status.NEW
        new_items = []
        for prod_id, cant in req.items.items():
            p = self.prod_api.get_producto(prod_id)
            if p is None:
                raise ValueError('producto {} no existe'.format(prod_id))
            if cant < 0:
                raise ValueError('Cantidad de producto {} es negativo'.format(prod_id))
            if cant > 0:
                new_items.append((req.meta.dest, prod_id, cant, p.nombre))
                if req.meta.trans_type == TransType.TRANSFER:
                    new_items.append((req.meta.origin, prod_id, -cant, p.nombre))

        t.items = new_items
        return t

    def save(self, request):
        """
        input TransferCreationRequest
        returns Transferencia
        """
        request.meta.timestamp = request.meta.timestamp or datetime.datetime.now()
        transfer = self.create_transfer_from_request(request)

        meta = transfer.meta
        filepath = os.path.join(meta.timestamp.date().isoformat(), uuid.uuid1().hex)
        db_entry = NTransferencia(
            date=meta.timestamp,
            origin=meta.origin,
            dest=meta.dest,
            trans_type=meta.trans_type,
            status=meta.status,
            items_location=filepath
            )
        self.db_session.add(db_entry)
        self.db_session.flush()
        transfer.meta.uid = db_entry.id
        self.filemanager.put_file(filepath, transfer.to_json())
        self.db_session.commit()
        return transfer

    def commit(self, uid):
        transfer = self.get_doc(uid)
        meta = transfer.meta
        if meta.status and meta.status != Status.NEW:
            return None
        transactions = TransApiDB.items_to_transactions(transfer)
        if not self.prod_api.exec_transactions_with_session(self.db_session, transactions):
            return None
        self.db_session.query(NTransferencia).filter_by(id=uid).update({'status': Status.COMITTED})
        self.db_session.commit()
        meta.status = Status.COMITTED
        return transfer

    def delete(self, uid):
        transfer = self.get_doc(uid)
        if transfer.meta.status != Status.COMITTED:
            return None
        transactions = TransApiDB.items_to_transactions(transfer)
        inversed = imap(Transaction.inverse, transactions) # revert transactions
        if not self.prod_api.exec_transactions_with_session(self.db_session, inversed):
            return None
        self.db_session.query(NTransferencia).filter_by(id=uid).update({'status': Status.DELETED})
        self.db_session.commit()
        transfer.meta.status = Status.DELETED
        return transfer

    @classmethod
    def items_to_transactions(cls, transfer):
        reason = 'transfer:' + str(transfer.meta.uid)
        for i in transfer.items:
            bodega_id, prod, cant, name = i
            yield Transaction(bodega_id, prod, cant, name, reason)


