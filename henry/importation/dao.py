# encoding=utf8
from decimal import Decimal

from henry.base.dbapi import dbmix
from henry.base.serialization import SerializableMixin, TypedSerializableMixin, parse_iso_datetime, json_dumps
from henry.dao.document import Status
from henry.product.dao import ProdItemGroup, InventoryMovement
from sqlalchemy import func
from .schema import (NUniversalProduct, NDeclaredGood, NPurchaseItem,
                     NPurchase, NSale, NInvMovementMeta, NEntity,
                     NInventory, NCustomItem)

NORMAL_FILTER_MULT = Decimal('0.35')

UniversalProd = dbmix(NUniversalProduct)
DeclaredGood = dbmix(NDeclaredGood)
PurchaseItem = dbmix(NPurchaseItem)
CustomItem = dbmix(NCustomItem)


class Purchase(dbmix(NPurchase)):
    @classmethod
    def deserialize(cls, thedict):
        result = super(Purchase, cls).deserialize(thedict)
        if thedict.get('total_gross_weight_kg', None):
            result.total_gross_weight_kg = Decimal(result.total_gross_weight_kg)
        if thedict.get('total_rmb', None):
            result.total_rmb = result.total_rmb
        if thedict.get('timestamp', None):
            result.timestamp = parse_iso_datetime(result.timestamp)
        return result


class PurchaseFull(SerializableMixin):
    _name = ('meta', 'items')

    def __init__(self, meta=None, items=None):
        self.meta = meta
        self.items = items


class PurchaseItemFull(SerializableMixin):
    _name = ('prod_detail', 'item')

    def __init__(self, prod_detail=None, item=None):
        self.prod_detail = prod_detail
        self.item = item


def get_purchase_item_full(dbapi, purchase_id):
    for item, prod in dbapi.db_session.query(
        NPurchaseItem, NUniversalProduct).filter(
        NPurchaseItem.purchase_id == purchase_id).filter(
        NPurchaseItem.upi == NUniversalProduct.upi):
        yield PurchaseItemFull(
            prod_detail=UniversalProd.from_db_instance(prod),
            item=PurchaseItem.from_db_instance(item))


def get_purchase_full(dbapi, uid):
    purchase = dbapi.get(uid, Purchase)
    full_items = list(get_purchase_item_full(dbapi, uid))
    return PurchaseFull(meta=purchase, items=full_items)


def create_custom(item, declared_map):
    display = declared_map.get(item.prod_detail.declaring_id, None)
    filters = None
    if display is None:
        display_name = ''
        filters = display.modify_strategy
    else:
        display_name = display.display_name
    normal_filter(item)
    price, quant, unit = item.item.price_rmb, item.item.quantity, item.prod_detail.unit
    if filters == 'docena':
        price, quant, unit = docen_filter(price, quant, unit)
    if filters == 'convert_to_kg':
        price, quant, unit = convert_to_kg(price, quant, unit, item.item.box)
    return CustomItem(
        display_name=display_name,
        quantity=quant,
        price_rmb=price,
        unit=ALL_UNITS[unit].name_es,
        box=item.item.box)


def generate_custom_for_purchase(dbapi, uid):
    declared = {x.uid: x for x in dbapi.search(DeclaredGood)}
    for item in get_purchase_item_full(dbapi, uid):
        custom = create_custom(item, declared)
        custom.purchase_id = uid
        custom_id = dbapi.create(custom)
        dbapi.update(item.item, {'custom_item_uid': custom_id})

class CustomItemFull(SerializableMixin):
    _name = ('custom', 'purchase_items')

    def __init__(self, custom=None, purchase_items=None):
        self.custom = custom
        self.purchase_items = purchase_items or []


def get_custom_items_full(dbapi, uid):
    item_full = get_purchase_item_full(dbapi, uid)
    items = {x.uid: CustomItemFull(x) for x in dbapi.search(CustomItem, purchase_id=uid)}
    for i in item_full:
        items[i.item.custom_item_uid].purchase_items.append(i)
    return sorted(items.values(), key=lambda i: i.custom.uid)


class InvMovementMeta(dbmix(NInvMovementMeta)):
    def merge_from(self, other):
        super(InvMovementMeta, self).merge_from(other)
        if getattr(self, 'value_usd', None):
            self.value_usd = Decimal(self.value_usd)
        if hasattr(self, 'timestamp') and (isinstance(self.timestamp, str)
                                           or isinstance(self.timestamp, unicode)):
            self.timestamp = parse_iso_datetime(self.timestamp)
        return self


Entity = dbmix(NEntity)


class ItemGroupCant(TypedSerializableMixin):
    _fields = (
        ('itemgroup', ProdItemGroup.deserialize),
        ('cant', Decimal)
    )


class InvMovementFull(TypedSerializableMixin):
    _fields = (
        ('meta', InvMovementMeta.deserialize),
        ('items', lambda x: map(ItemGroupCant.deserialize, x))
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

        transactions = map(make_inv_movement, invmo.items)
        self.inventoryapi.bulk_save(transactions)
        return invmo


class Sale(dbmix(NSale)):
    def merge_from(self, other):
        super(Sale, self).merge_from(other)
        if getattr(self, 'total_usd', None):
            self.total_usd = Decimal(self.total_usd)
        if getattr(self, 'tax_usd', None):
            self.tax_usd = Decimal(self.tax_usd)
        if hasattr(self, 'timestamp') and (isinstance(self.timestamp, str)
                                           or isinstance(self.timestamp, unicode)):
            self.timestamp = parse_iso_datetime(self.timestamp)
        return self


def get_sales_by_date_and_user(dbapi, start_date, end_date):
    for date, codename, user, pretax, tax in dbapi.db_session.query(
            func.DATE(NSale.timestamp), NSale.seller_codename,
            NSale.user_id,
            func.sum(NSale.pretax_amount_usd),
            func.sum(NSale.tax_usd)):
        yield date, codename, user, (pretax or 0) + (tax or 0)


Inventory = dbmix(NInventory)


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

class Unit(TypedSerializableMixin):
    LENGTH = 'length'
    WEIGHT = 'weight'
    UNIT = 'unit'

    _fields = (
        ('uid', str),
        ('name_zh', unicode),
        ('name_es', unicode),
        ('type', str),
        ('equiv_base', str),
        ('equiv_multiplier', Decimal)
    )

def normal_filter(item):
    item.item.price_rmb *= NORMAL_FILTER_MULT
    return item

def docen_filter(price, quantity, unit):
    return price * 12, quantity / 12, ALL_UNITS['doz']

def convert_to_kg(price, quantity, unit, box=None):
    if unit.uid == 'kg':
        return price, quantity, unit

    # if unit converts to kg
    if unit.equiv_base == 'kg':
        mult = unit.equiv_multiplier
        return price / mult, quantity * mult, ALL_UNITS['kg']

    if box is not None:
        return 0, box * 30, ALL_UNITS['kg']

ALL_UNITS = {
    'kg': Unit(uid='kg', name_zh=u'公斤', name_es='kilogramo', equiv_base=None,
               equiv_multiplier=1, type=Unit.WEIGHT),
    'm': Unit(uid='m', name_zh=u'米', name_es='metro', equiv_base=None,
              equiv_multiplier=1, type=Unit.LENGTH),
    'ge': Unit(uid='ge', name_zh=u'个', name_es='unidad', equiv_base=None,
               equiv_multiplier=1, type=Unit.UNIT),
    'p': Unit(uid='p', name_zh=u'包', name_es='paquete', equiv_base=None,
              equiv_multiplier=1, type=Unit.UNIT),
    'r': Unit(uid='r', name_zh=u'卷', name_es='rollo', equiv_base=None,
              equiv_multiplier=1, type=Unit.UNIT),
    't': Unit(uid='t', name_zh=u'条', name_es='tira', equiv_base=None,
              equiv_multiplier=1, type=Unit.UNIT),
    'y': Unit(uid='y', name_zh=u'码', name_es='yarda', equiv_base='m',
              equiv_multiplier='0.9144', type=Unit.LENGTH),
    'jin': Unit(uid='jin', name_zh=u'斤', name_es='paquete de 0.5kg',
                equiv_base='kg',
                equiv_multiplier='0.5', type=Unit.WEIGHT),
    'zh': Unit(uid='jin', name_zh=u'长', name_es='hoja',
                equiv_base=None,
                equiv_multiplier='1', type=Unit.UNIT),
    'p350m': Unit(uid='350m', name_zh=u'350米一卷', name_es='paquete de 350m', equiv_base='m',
                  equiv_multiplier=350, type=Unit.LENGTH),
    'p450g': Unit(uid='p450g', name_zh=u'450g一包', name_es='paquete de 450g', equiv_base='kg',
                  equiv_multiplier='0.45', type=Unit.WEIGHT),
    'p350g': Unit(uid='p350g', name_zh=u'350g一包', name_es='paquete de 350g', equiv_base='kg',
                  equiv_multiplier='0.35', type=Unit.WEIGHT),
    'p10y': Unit(uid='p10y', name_zh=u'10码一包', name_es='rollo de 10yardas', equiv_base='m',
                 equiv_multiplier='91.44', type=Unit.LENGTH),
    'p15y': Unit(uid='p15y', name_zh=u'15码一包', name_es='rollo de 15yardas', equiv_base='m',
                 equiv_multiplier='13.716', type=Unit.WEIGHT),
    'p100y': Unit(uid='p100y', name_zh=u'100码一包', name_es='rollo de 100yardas', equiv_base='m',
                  equiv_multiplier='914.4', type=Unit.WEIGHT),
    'p100ge': Unit(uid='p100ge', name_zh=u'100粒一包', name_es='paquete de 100', equiv_base='ge',
                   equiv_multiplier='100', type=Unit.UNIT),
    'p200ge': Unit(uid='p200ge', name_zh=u'200粒一包', name_es='paquete de 200', equiv_base='ge',
                   equiv_multiplier='200', type=Unit.UNIT),
    'p500ge': Unit(uid='p500ge', name_zh=u'500粒一包', name_es='paquete de 500', equiv_base='ge',
                   equiv_multiplier='500', type=Unit.UNIT),
    'p1000ge': Unit(uid='p1000ge', name_zh=u'1000粒一包', name_es='paquete de 1000', equiv_base='ge',
                    equiv_multiplier='1000', type=Unit.UNIT),
    'p2000ge': Unit(uid='p2000ge', name_zh=u'2000粒一包', name_es='paquete de 2000', equiv_base='ge',
                    equiv_multiplier='2000', type=Unit.UNIT),
    'p5000ge': Unit(uid='p5000ge', name_zh=u'5000粒一包', name_es='paquete de 5000', equiv_base='ge',
                    equiv_multiplier='5000', type=Unit.UNIT),
    'doz': Unit(uid='doz', name_zh=u'打', name_es='docena', equiv_base='ge',
                    equiv_multiplier='12', type=Unit.UNIT),
}
