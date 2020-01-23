from builtins import map
from builtins import object
from decimal import Decimal
from sqlalchemy import func
from henry.dao.document import Status
from henry.base.dbapi import dbmix
from henry.base.serialization import parse_iso_datetime, TypedSerializableMixin, json_dumps
from henry.product.dao import ProdItemGroup, InventoryMovement

from .schema import NInventory, NSale, NInvMovementMeta, NEntity

__author__ = 'han'

Inventory = dbmix(NInventory)
Entity = dbmix(NEntity)

def client_sale_report(dbapi, start, end):
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


class InvMovementMeta(dbmix(NInvMovementMeta)):  # type: ignore
    def merge_from(self, other):
        super(InvMovementMeta, self).merge_from(other)
        if getattr(self, 'value_usd', None):
            self.value_usd = Decimal(self.value_usd)
        if hasattr(self, 'timestamp') and (isinstance(self.timestamp, str)
                                           or isinstance(self.timestamp, str)):
            self.timestamp = parse_iso_datetime(self.timestamp)
        return self


class ItemGroupCant(TypedSerializableMixin):
    _fields = (
        ('itemgroup', ProdItemGroup.deserialize),
        ('cant', Decimal)
    )


class InvMovementFull(TypedSerializableMixin):
    _fields = (
        ('meta', InvMovementMeta.deserialize),
        ('items', lambda x: list(map(ItemGroupCant.deserialize, x)))
    )


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


class Sale(dbmix(NSale)):  # type: ignore
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
    inv = dbapi.getone(Inventory, entity_codename=codename, external_id=external_id)
    if not inv:
        largest_id = dbapi.db_session.query(func.max(NInventory.inventory_id)).first()[0] or 0
        inv = Inventory(entity_codename=codename, external_id=external_id, inventory_id=largest_id + 1)
        dbapi.create(inv)
    return inv.inventory_id


class SaleReportByDate(TypedSerializableMixin):
    _fields = (
        ('timestamp', parse_iso_datetime),
        ('ruc', str),
        ('sale_pretax_usd', Decimal),
        ('tax_usd', Decimal),
        ('count', int)
    )