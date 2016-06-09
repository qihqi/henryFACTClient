import datetime
import os
import uuid
from decimal import Decimal

from henry.base.serialization import SerializableMixin, DbMixin, parse_iso_datetime
from henry.dao.document import MetaItemSet, Item
from henry.product.dao import PriceList, ProdItemGroup, InvMovementType, InventoryMovement

from .schema import NTransferencia


class TransType:
    INGRESS = 'INGRESO'
    TRANSFER = 'TRANSFER'
    EXTERNAL = 'EXTERNA'
    EGRESS = 'EGRESO'

    names = (INGRESS,
             TRANSFER,
             EXTERNAL,
             EGRESS)


class TransMetadata(SerializableMixin, DbMixin):
    _db_attr = {
        'uid': 'id',
        'origin': 'origin',
        'dest': 'dest',
        'user': 'user',
        'trans_type': 'trans_type',
        'ref': 'ref',
        'timestamp': 'timestamp',
        'status': 'status',
        'value': 'value'}
    _name = _db_attr.keys()
    _db_class = NTransferencia

    def __init__(self,
                 trans_type=None,
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
        self.timestamp = timestamp if timestamp else datetime.datetime.now()
        self.status = status

    @classmethod
    def deserialize(cls, the_dict):
        x = super(cls, TransMetadata).deserialize(the_dict)
        if not isinstance(x.timestamp, datetime.datetime):
            x.timestamp = parse_iso_datetime(x.timestamp)
        return x


class TransItem(Item):
    @classmethod
    def deserialize(cls, the_dict):
        if 'name' in the_dict['prod'] and 'prod_id' in the_dict['prod']:
            prod = ProdItemGroup.deserialize(the_dict['prod'])
        else:
            price = PriceList.deserialize(the_dict['prod'])
            prod = ProdItemGroup(prod_id=price.prod_id, name=price.nombre)
        cant = Decimal(the_dict['cant'])
        return cls(prod, cant)


def _convert_type(tipo):
    if tipo == TransType.INGRESS:
        return InvMovementType.INGRESS
    if tipo == TransType.EGRESS:
        return InvMovementType.EGRESS
    if tipo == TransType.EXTERNAL:
        return InvMovementType.EGRESS
    if tipo == TransType.TRANSFER:
        return InvMovementType.TRANSFER

class Transferencia(MetaItemSet):
    _metadata_cls = TransMetadata

    def items_to_transaction(self, _dbapi):
        tipo = self.meta.trans_type
        for item in self.items:
            yield InventoryMovement(
                from_inv_id=self.meta.origin or -1,
                to_inv_id=self.meta.dest or -1,
                quantity=item.cant,
                prod_id=item.prod.prod_id,
                itemgroup_id=item.prod.uid,
                type=_convert_type(tipo),
                reference_id=str(self.meta.uid),
            )

    def validate(self):
        if self.meta.trans_type not in (TransType.EXTERNAL, TransType.EGRESS):
            if self.meta.dest is None:
                raise ValueError('dest is none for non external')
        else:
            self.meta.dest = None
        if self.meta.trans_type != TransType.INGRESS:
            if self.meta.origin is None:
                raise ValueError('origin is none for non ingress')
        else:
            self.meta.origin = None

    @property
    def filepath_format(self):
        path = getattr(self, '_path', None)
        if path is None:
            self._path = os.path.join(
                self.meta.timestamp.date().isoformat(), uuid.uuid1().hex)
        return self._path

    @classmethod
    def deserialize(cls, the_dict):
        x = cls()
        x.meta = cls._metadata_cls.deserialize(the_dict['meta'])
        x.items = map(TransItem.deserialize, the_dict['items'])
        return x


