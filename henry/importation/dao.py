# encoding=utf8
from decimal import Decimal
import functools

from henry.base.dbapi import dbmix
from henry.base.serialization import SerializableMixin, TypedSerializableMixin, parse_iso_datetime
from .schema import (NUniversalProduct, NDeclaredGood, NPurchaseItem,
                     NPurchase, NCustomItem)
from henry.sale_records.schema import NEntity

NORMAL_FILTER_MULT = Decimal('0.35')

UniversalProd = dbmix(NUniversalProduct)
DeclaredGood = dbmix(NDeclaredGood)
PurchaseItem = dbmix(NPurchaseItem)

class CustomItem(dbmix(NCustomItem)):
    @classmethod
    def deserialize(cls, thedict):
        result = super(CustomItem, cls).deserialize(thedict)
        if thedict.get('box', None):
            result.box = Decimal(result.box)
        if thedict.get('price_rmb', None):
            result.price_rmb = Decimal(result.price_rmb)
        if thedict.get('quantity', None):
            result.quantity = Decimal(result.quantity)
        return result


class PurchaseStatus:
    NEW = 'NEW'
    READY = 'READY'
    CUSTOM = 'CUSTOM'


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


class PurchaseItemFull(TypedSerializableMixin):
    _fields = (
        ('prod_detail', UniversalProd.deserialize),
        ('item', PurchaseItem.deserialize))

    def __init__(self, prod_detail=None, item=None):
        self.prod_detail = prod_detail
        self.item = item


def _get_purchase_item_full_filter(dbapi, filter_):
    for item, prod in dbapi.db_session.query(
            NPurchaseItem, NUniversalProduct).filter(
            NPurchaseItem.upi == NUniversalProduct.upi).filter(filter_):
        yield PurchaseItemFull(
            prod_detail=UniversalProd.from_db_instance(prod),
            item=PurchaseItem.from_db_instance(item))


def get_purchase_item_full(dbapi, uid):
    return _get_purchase_item_full_filter(dbapi, NPurchaseItem.purchase_id == uid)


def get_purchase_item_full_by_custom(dbapi, uid):
    return _get_purchase_item_full_filter(dbapi, NPurchaseItem.custom_item_uid == uid)


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
        purchase_id=item.item.purchase_id,
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

class CustomItemFull(TypedSerializableMixin):
    _fields = (
        ('custom', CustomItem.deserialize),
        ('purchase_items', functools.partial(map, PurchaseItemFull.deserialize))
    )

    def __init__(self, custom=None, purchase_items=None):
        self.custom = custom
        self.purchase_items = purchase_items or []


def get_custom_items_full(dbapi, uid):
    item_full = map(normal_filter, get_purchase_item_full(dbapi, uid))
    items = {x.uid: CustomItemFull(x) for x in dbapi.search(CustomItem, purchase_id=uid)}
    for i in item_full:
        items[i.item.custom_item_uid].purchase_items.append(i)
    return sorted(items.values(), key=lambda i: i.custom.uid)


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
