import dataclasses
import datetime
from decimal import Decimal
from sqlalchemy import func
from typing import Optional, Iterator, List

from henry.base.dbapi import SerializableDB, DBApiGeneric
from henry.dao.document import Status
from henry.base.serialization import parse_iso_datetime, json_dumps, SerializableData
from henry.product.dao import ProdItemGroup, InventoryMovement

from .schema import NInventory, NSale, NInvMovementMeta, NEntity

__author__ = 'han'


@dataclasses.dataclass
class Inventory(SerializableDB[NInventory]):
    db_class = NInventory
    uid: Optional[int] = None
    entity_codename: Optional[str] = None
    external_id: Optional[int] = None
    inventory_id: Optional[int] = None
    name: Optional[str] = None


@dataclasses.dataclass
class Entity(SerializableDB[NEntity]):
    db_class = NEntity
    codename: Optional[str] = None
    name: Optional[str] = None
    desc: Optional[str] = None


@dataclasses.dataclass
class SaleReportByDate(SerializableData):
    timestamp: Optional[datetime.datetime]
    ruc: Optional[str]
    sale_pretax_usd: Optional[Decimal]
    tax_usd: Optional[Decimal]
    count: Optional[int]


def client_sale_report(
        dbapi: DBApiGeneric,
        start: datetime.date,
        end: datetime.date) -> Iterator[SaleReportByDate]:
    sales_by_date = list(dbapi.db_session.query(
        NSale.seller_ruc,
        func.date(NSale.timestamp), func.sum(NSale.pretax_amount_usd),
        func.sum(NSale.tax_usd), func.count(NSale.uid)).filter(
        NSale.timestamp >= start, NSale.timestamp <= end,
        NSale.status == Status.NEW, NSale.payment_format != 'None').group_by(
        func.date(NSale.timestamp), NSale.seller_ruc))
    for ruc, date, sale, tax, count in sales_by_date:
        yield SaleReportByDate(
            timestamp=date, ruc=ruc, sale_pretax_usd=sale,
            tax_usd=tax, count=count
        )


@dataclasses.dataclass
class InvMovementMeta(SerializableDB[NInvMovementMeta]):
    db_class = NInvMovementMeta
    uid: Optional[int] = None
    inventory_codename: Optional[str] = None
    inventory_docid: Optional[int] = None

    timestamp: Optional[datetime.datetime] = None
    status: Optional[str] = None

    origin: Optional[int] = None
    dest: Optional[int] = None

    trans_type: Optional[str] = None
    value_usd: Optional[Decimal] = None

    # unix filepath where the items is stored
    items_location: Optional[str] = None

    def merge_from(self, other):
        super(InvMovementMeta, self).merge_from(other)
        if getattr(self, 'value_usd', None):
            self.value_usd = Decimal(self.value_usd)
        if hasattr(self, 'timestamp') and (isinstance(self.timestamp, str)
                                           or isinstance(self.timestamp, str)):
            self.timestamp = parse_iso_datetime(self.timestamp)
        return self


@dataclasses.dataclass
class ItemGroupCant(SerializableData):
    itemgroup: ProdItemGroup = ProdItemGroup()
    cant: Optional[Decimal] = None


@dataclasses.dataclass
class InvMovementFull(SerializableData):
    meta: InvMovementMeta = InvMovementMeta()
    items: List[ItemGroupCant] = dataclasses.field(default_factory=lambda: [])


class InvMovementManager(object):
    def __init__(self, dbapi, fileservice, inventoryapi):
        self.dbapi = dbapi
        self.fileservice = fileservice
        self.inventoryapi = inventoryapi

    def create(self, invmo):
        datestr = invmo.meta.timestamp.date().isoformat()
        name = '{}/{}-{}-{}'.format(datestr, invmo.meta.inventory_codename,
                                    invmo.meta.trans_type,
                                    invmo.meta.inventory_docid)
        path = self.fileservice.make_fullpath(name)
        invmo.meta.items_location = path
        self.dbapi.create(invmo.meta)
        self.fileservice.put_file(name, json_dumps(invmo.serialize()))

        # execute transactions
        def make_inv_movement(itemgroupcant):
            inv = InventoryMovement()
            inv.from_inv_id = invmo.meta.origin
            inv.to_inv_id = invmo.meta.dest
            inv.quantity = itemgroupcant.cant
            inv.prod_id = itemgroupcant.itemgroup.prod_id
            inv.itemgroup_id = itemgroupcant.itemgroup.uid
            inv.timestamp = invmo.meta.timestamp
            inv.type = invmo.meta.trans_type
            inv.reference_id = invmo.meta.uid
            return inv

        transactions = list(map(make_inv_movement, invmo.items))
        self.inventoryapi.bulk_save(transactions)
        return invmo


@dataclasses.dataclass
class Sale(SerializableDB[NSale]):
    db_class = NSale
    uid: Optional[int] = None
    timestamp: Optional[datetime.datetime] = None
    client_id: Optional[str] = None
    seller_codename: Optional[str] = None
    seller_ruc: Optional[str] = None
    seller_inv_uid: Optional[int] = None
    invoice_code: Optional[str] = None
    pretax_amount_usd: Optional[Decimal] = None
    tax_usd: Optional[Decimal] = None
    status: Optional[str] = None
    user_id: Optional[str] = None
    payment_format: Optional[str] = None

    def merge_from(self, other):
        super(Sale, self).merge_from(other)
        if getattr(self, 'total_usd', None):
            self.total_usd = Decimal(self.total_usd)
        if getattr(self, 'tax_usd', None):
            self.tax_usd = Decimal(self.tax_usd)
        if hasattr(self, 'timestamp') and (isinstance(self.timestamp, str)
                                           or isinstance(self.timestamp, str)):
            self.timestamp = parse_iso_datetime(self.timestamp)
        return self


def get_sales_by_date_and_user(dbapi, start_date, end_date):
    for date, codename, user, pretax, tax in dbapi.db_session.query(
            func.DATE(NSale.timestamp), NSale.seller_codename,
            NSale.user_id,
            func.sum(NSale.pretax_amount_usd),
            func.sum(NSale.tax_usd)):
        yield date, codename, user, (pretax or 0) + (tax or 0)


def get_or_create_inventory_id(dbapi, codename, external_id):
    if external_id == -1:
        return -1
    inv = dbapi.getone(
        Inventory,
        entity_codename=codename,
        external_id=external_id)
    if not inv:
        largest_id = dbapi.db_session.query(
            func.max(NInventory.inventory_id)).first()[0] or 0
        inv = Inventory(
            entity_codename=codename,
            external_id=external_id,
            inventory_id=largest_id + 1)
        dbapi.create(inv)
    return inv.inventory_id
