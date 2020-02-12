import dataclasses
import datetime
import os
import uuid
from decimal import Decimal

from henry.base.dbapi import SerializableDB
from henry.base.serialization import parse_iso_datetime, SerializableData
from henry.dao.document import MetaItemSet, Item
from henry.product.dao import PriceList, ProdItemGroup, InvMovementType, InventoryMovement, ProdItem

from .schema import NTransferencia
from typing import Dict, Type, Iterator, Optional, List


class TransType(object):
    INGRESS = 'INGRESO'
    TRANSFER = 'TRANSFER'
    EXTERNAL = 'EXTERNA'
    EGRESS = 'EGRESO'

    names = (INGRESS,
             TRANSFER,
             EXTERNAL,
             EGRESS)


@dataclasses.dataclass
class TransMetadata(SerializableDB[NTransferencia]):
    db_class = NTransferencia
    uid: Optional[int] = None
    timestamp: Optional[datetime.datetime] = None
    status: Optional[str] = None
    origin: Optional[int] = None
    dest: Optional[int] = None
    trans_type: Optional[str] = None
    ref: Optional[str] = None
    value: Optional[Decimal] = None
    items_location: Optional[str] = dataclasses.field(default=None, metadata={
        'skip': True})

    @classmethod
    def deserialize(cls, the_dict):
        x = super(cls, TransMetadata).deserialize(the_dict)
        if not isinstance(x.timestamp, datetime.datetime):
            x.timestamp = parse_iso_datetime(x.timestamp)
        return x


@dataclasses.dataclass
class TransItem(SerializableData):
    prod: ProdItemGroup = ProdItemGroup()
    cant: Decimal = Decimal(0)

    @classmethod
    def deserialize(cls, the_dict: Dict) -> 'TransItem':
        if 'name' in the_dict['prod'] and 'prod_id' in the_dict['prod']:
            prod = ProdItemGroup.deserialize(the_dict['prod'])
        else:
            price = PriceList.deserialize(the_dict['prod'])
            prod = ProdItemGroup(prod_id=price.prod_id, name=price.nombre)  # type: ignore
        cant = Decimal(the_dict['cant'])
        return cls(prod, cant)


def transtype_to_invtype(tipo):
    if tipo == TransType.INGRESS:
        return InvMovementType.INGRESS
    if tipo == TransType.EGRESS:
        return InvMovementType.EGRESS
    if tipo == TransType.EXTERNAL:
        return InvMovementType.EGRESS
    if tipo == TransType.TRANSFER:
        return InvMovementType.TRANSFER

@dataclasses.dataclass
class Transferencia(SerializableData, MetaItemSet):
    _metadata_cls = TransMetadata
    meta: TransMetadata
    items: List[TransItem]

    def items_to_transaction(self, dbapi=None):
        # NOTE: type of item.prod is ProdItemGroup here
        del dbapi
        tipo = self.meta.trans_type
        for item in self.items:
            yield InventoryMovement(
                from_inv_id=self.meta.origin or -1,
                to_inv_id=self.meta.dest or -1,
                quantity=item.cant,
                prod_id=item.prod.prod_id,
                itemgroup_id=item.prod.uid,
                type=transtype_to_invtype(tipo),
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
    def filepath_format(self) -> str:
        path = getattr(self, '_path', None)
        if path is None:
            assert self.meta.timestamp is not None
            self._path = os.path.join(
                self.meta.timestamp.date().isoformat(), uuid.uuid1().hex)
        return self._path
