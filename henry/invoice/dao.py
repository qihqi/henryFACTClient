import dataclasses
import datetime
import os
import uuid
from decimal import Decimal
from typing import Optional, Iterator
from henry.base.serialization import parse_iso_datetime
from henry.base.dbapi import SerializableDB
from henry.dao.document import MetaItemSet
from henry.product.dao import InventoryMovement, ProdItem, InvMovementType, get_real_prod_id
from henry.users.dao import Client, User

from .coreschema import NNota, NNotaExtra
from .schema import NSRINota

__author__ = 'han'


class PaymentFormat(object):
    CASH = "efectivo"
    CARD = "tarjeta"
    CHECK = "cheque"
    DEPOSIT = "deposito"
    CREDIT = "credito"
    VARIOUS = "varios"
    names = (
        CASH,
        CARD,
        CHECK,
        DEPOSIT,
        CREDIT,
        VARIOUS,
    )


@dataclasses.dataclass
class InvMetadata(SerializableDB[NNota]):
    db_class = NNota
    _pkey_name = 'uid'
    uid: Optional[int] = None
    timestamp: Optional[datetime.datetime] = None
    status: Optional[str] = None

    # this pair should be unique
    codigo: Optional[str] = None
    almacen_id: Optional[int] = None
    almacen_name: Optional[str] = None
    almacen_ruc: Optional[str] = None

    # client_id: Optional[str] = None
    user: Optional[str] = None
    client: Optional[Client] = None
    paid: Optional[bool] = None
    paid_amount: Optional[int] = None
    payment_format: Optional[str] = None

    subtotal: Optional[int] = None
    total: Optional[int] = None
    tax: Optional[int] = None
    retension: Optional[int] = None
    discount: Optional[int] = None
    tax_percent: Optional[int] = None
    discount_percent: Optional[int] = None

    bodega_id: Optional[int] = None
    items_location: Optional[str] = dataclasses.field(default=None, metadata={
        'skip': True})

    @classmethod
    def deserialize(cls, the_dict) -> 'InvMetadata':
        x = cls().merge_from(the_dict)
        if x.timestamp and not isinstance(x.timestamp, datetime.datetime):
            x.timestamp = parse_iso_datetime(x.timestamp)
        if 'client' in the_dict:
            client = Client.deserialize(the_dict['client'])
            x.client = client
        else:
            x.client = None
        return x

    def db_instance(self):
        db_instance = super(InvMetadata, self).db_instance()
        db_instance.client_id = self.client.codigo
        return db_instance

    @classmethod
    def from_db_instance(cls, db_instance):
        this = super(InvMetadata, cls).from_db_instance(db_instance)
        this.client = Client()
        this.client.codigo = db_instance.client_id
        return this


class Invoice(MetaItemSet[InvMetadata]):
    _metadata_cls = InvMetadata

    def items_to_transaction(self, dbapi) -> Iterator[InventoryMovement]:
        assert self.meta is not None, 'Meta is None!'
        for item in self.items:
            proditem = dbapi.getone(ProdItem, prod_id=item.prod.prod_id)
            # TODO: deprecate use of upi at all
            inv_id = item.prod.upi or self.meta.bodega_id
            assert item.prod.multiplicador is not None
            yield InventoryMovement(
                from_inv_id=inv_id,
                to_inv_id=-1,
                quantity=(item.cant * item.prod.multiplicador),
                prod_id=get_real_prod_id(item.prod.prod_id),
                itemgroup_id=proditem.itemgroupid,
                type=InvMovementType.SALE,
                reference_id=str(self.meta.uid),
            )

    def validate(self):
        if getattr(self.meta, 'codigo', None) is None:
            raise ValueError('codigo cannot be None to save an invoice')

    @property
    def filepath_format(self):
        path = getattr(self, '_path', None)
        if path is None:
            self._path = os.path.join(
                self.meta.timestamp.date().isoformat(), uuid.uuid1().hex)
        return self._path


class SRINotaStatus:
    CREATED = 'created'
    CREATED_SENT = 'created_sent'
    CREATED_SENT_VALIDATED = 'created_sent_validated'
    DELETED = 'deleted'
    DELETED_SENT = 'deleted_sent'
    DELETED_SENT_VALIDATED = 'deleted_sent_validated'


@dataclasses.dataclass
class NotaExtra(SerializableDB[NNotaExtra]):
    db_class = NNotaExtra
    uid: Optional[int] = None
    status: Optional[str] = None
    last_change_time: Optional[datetime.datetime] = None

@dataclasses.dataclass
class SRINota(SerializableDB[NSRINota]):
    db_class = NSRINota
    uid : Optional[int] = None
    almacen_ruc : Optional[str] = None
    orig_codigo : Optional[str] = None
    timestamp_received: Optional[datetime.datetime] = None
    status : Optional[str] = None
    orig_timestamp: Optional[datetime.datetime] = None
    buyer_ruc: Optional[str] = None
    buyer_name: Optional[str] = None
    total: Optional[Decimal] = None
    tax: Optional[Decimal] = None

    json_inv_location : Optional[str] = None
    xml_inv_location : Optional[str] = None
    resp1_location : Optional[str] = None
    resp2_location : Optional[str] = None
