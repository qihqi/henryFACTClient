# encoding=utf8
import dataclasses
import datetime
from typing import Optional, List

from decimal import Decimal
import functools

from past.utils import old_div

from henry.base.dbapi import SerializableDB
from henry.base.serialization import SerializableMixin, parse_iso_datetime, SerializableData
from .schema import (NUniversalProduct, NDeclaredGood, NPurchaseItem,
                     NPurchase, NCustomItem, NUnit)

NORMAL_FILTER_MULT = Decimal('0.35')


@dataclasses.dataclass
class Unit(SerializableDB[NUnit]):
    LENGTH = 'length'
    WEIGHT = 'weight'
    UNIT = 'unit'
    db_class = NUnit
    uid : Optional[str] = None
    name_zh : Optional[str] = None
    name_es : Optional[str] = None
    type : Optional[str] = None
    equiv_base: Optional[str] = None
    equiv_multiplier : Optional[Decimal] = None

ALL_UNITS = {
    'kg': Unit(uid='kg', name_zh=u'公斤', name_es='kilogramo', equiv_base=None,
               equiv_multiplier=Decimal(1),type=Unit.WEIGHT),
    'm': Unit(uid='m', name_zh=u'米', name_es='metro', equiv_base=None,
              equiv_multiplier=Decimal(1),type=Unit.LENGTH),
    'ge': Unit(uid='ge', name_zh=u'个', name_es='unidad', equiv_base=None,
               equiv_multiplier=Decimal(1),type=Unit.UNIT),
    'p': Unit(uid='p', name_zh=u'包', name_es='paquete', equiv_base=None,
              equiv_multiplier=Decimal(1),type=Unit.UNIT),
    'r': Unit(uid='r', name_zh=u'卷', name_es='rollo', equiv_base=None,
              equiv_multiplier=Decimal(1),type=Unit.UNIT),
    't': Unit(uid='t', name_zh=u'条', name_es='tira', equiv_base=None,
              equiv_multiplier=Decimal(1),type=Unit.UNIT),
    'y': Unit(uid='y', name_zh=u'码', name_es='yarda', equiv_base='m',
              equiv_multiplier=Decimal('0.9144'),type=Unit.LENGTH),
    'jin': Unit(uid='jin', name_zh=u'斤', name_es='paquete de 0.5kg',
                equiv_base='kg',
                equiv_multiplier=Decimal('0.5'),type=Unit.WEIGHT),
    'zh': Unit(uid='zh', name_zh=u'张', name_es='hoja',
                equiv_base=None,
                equiv_multiplier=Decimal('1'),type=Unit.UNIT),
    'p350m': Unit(uid='p350m', name_zh=u'350米一卷', name_es='paquete de 350m', equiv_base='m',
                  equiv_multiplier=Decimal(350),type=Unit.LENGTH),
    'p450g': Unit(uid='p450g', name_zh=u'450g一包', name_es='paquete de 450g', equiv_base='kg',
                  equiv_multiplier=Decimal('0.45'),type=Unit.WEIGHT),
    'p350g': Unit(uid='p350g', name_zh=u'350g一包', name_es='paquete de 350g', equiv_base='kg',
                  equiv_multiplier=Decimal('0.35'),type=Unit.WEIGHT),
    'p10y': Unit(uid='p10y', name_zh=u'10码一包', name_es='rollo de 10yardas', equiv_base='m',
                 equiv_multiplier=Decimal('91.44'),type=Unit.LENGTH),
    'p15y': Unit(uid='p15y', name_zh=u'15码一包', name_es='rollo de 15yardas', equiv_base='m',
                 equiv_multiplier=Decimal('13.716'),type=Unit.WEIGHT),
    'p100y': Unit(uid='p100y', name_zh=u'100码一包', name_es='rollo de 100yardas', equiv_base='m',
                  equiv_multiplier=Decimal('914.4'),type=Unit.WEIGHT),
    'p100ge': Unit(uid='p100ge', name_zh=u'100粒一包', name_es='paquete de 100', equiv_base='ge',
                   equiv_multiplier=Decimal('100'),type=Unit.UNIT),
    'p200ge': Unit(uid='p200ge', name_zh=u'200粒一包', name_es='paquete de 200', equiv_base='ge',
                   equiv_multiplier=Decimal('200'),type=Unit.UNIT),
    'p500ge': Unit(uid='p500ge', name_zh=u'500粒一包', name_es='paquete de 500', equiv_base='ge',
                   equiv_multiplier=Decimal('500'),type=Unit.UNIT),
    'p1000ge': Unit(uid='p1000ge', name_zh=u'1000粒一包', name_es='paquete de 1000', equiv_base='ge',
                    equiv_multiplier=Decimal('1000'),type=Unit.UNIT),
    'p2000ge': Unit(uid='p2000ge', name_zh=u'2000粒一包', name_es='paquete de 2000', equiv_base='ge',
                    equiv_multiplier=Decimal('2000'),type=Unit.UNIT),
    'p5000ge': Unit(uid='p5000ge', name_zh=u'5000粒一包', name_es='paquete de 5000', equiv_base='ge',
                    equiv_multiplier=Decimal('5000'),type=Unit.UNIT),
    'doz': Unit(uid='doz', name_zh=u'打', name_es='docena', equiv_base='ge',
                    equiv_multiplier=Decimal('12'),type=Unit.UNIT),
}

@dataclasses.dataclass
class UniversalProd(SerializableDB[NUniversalProduct]):
    db_class = NUniversalProduct
    upi : Optional[int] = None
    name_es : Optional[str] = None
    name_zh : Optional[str] = None
    providor_zh : Optional[str] = None
    providor_item_id : Optional[str] = None
    selling_id : Optional[str] = None
    declaring_id : Optional[int] = None
    material : Optional[str] = None
    unit : Optional[str] = None
    description : Optional[str] = None
    thumbpath : Optional[str] = None

@dataclasses.dataclass
class DeclaredGood(SerializableDB[NDeclaredGood]):
    db_class = NDeclaredGood
    uid : Optional[int] = None
    display_name : Optional[str] = None
    display_price : Optional[Decimal] = None
    box_code : Optional[str] = None
    modify_strategy : Optional[str] = None


@dataclasses.dataclass
class PurchaseItem(SerializableDB[NPurchaseItem]):
    db_class = NPurchaseItem
    uid : Optional[int] = None
    purchase_id : Optional[int] = None
    upi : Optional[int] = None
    color : Optional[str] = None
    quantity : Optional[Decimal] = None
    price_rmb : Optional[Decimal] = None
    box : Optional[Decimal] = None
    custom_item_uid : Optional[int] = None

    @classmethod
    def deserialize(cls, thedict):
        result = super(PurchaseItem, cls).deserialize(thedict)
        if thedict.get('box', None):
            result.box = Decimal(result.box)
        if thedict.get('box') == '':
            result.box = None
        if thedict.get('price_rmb', None):
            result.price_rmb = Decimal(result.price_rmb)
        if thedict.get('quantity', None):
            result.quantity = Decimal(result.quantity)
        return result


@dataclasses.dataclass
class CustomItem(SerializableDB[NCustomItem]):
    db_class = NCustomItem
    uid : Optional[int] = None
    purchase_id : Optional[int] = None
    display_name : Optional[str] = None
    quantity : Optional[Decimal] = None
    price_rmb : Optional[Decimal] = None
    unit : Optional[str] = None
    box : Optional[Decimal] = None
    box_code : Optional[str] = None

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


class PurchaseStatus(object):
    NEW = 'NEW'
    READY = 'READY'
    CUSTOM = 'CUSTOM'


@dataclasses.dataclass
class Purchase(SerializableDB[NPurchase]):
    db_class = NPurchase
    uid : Optional[int] = None
    timestamp : Optional[datetime.datetime] = None
    last_edit_timestamp : Optional[datetime.datetime] = None
    providor : Optional[str] = None
    total_rmb : Optional[Decimal] = None
    created_by : Optional[str] = None
    total_box : Optional[int] = None
    total_gross_weight_kg : Optional[Decimal] = None
    status : Optional[str] = None

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


@dataclasses.dataclass
class PurchaseItemFull(SerializableData):
    prod_detail: UniversalProd = UniversalProd()
    item: PurchaseItem = PurchaseItem()


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


def create_custom(item, declared_map, all_units):
    display = declared_map.get(item.prod_detail.declaring_id, None)
    filters = None
    if display is None:
        display_name = ''
    else:
        display_name = display.display_name
        filters = display.modify_strategy
    normal_filter(item)
    price, quant, unit = item.item.price_rmb, item.item.quantity, item.prod_detail.unit
    unit = all_units[unit]
    if filters == 'docena':
        price, quant, unit = docen_filter(price, quant, unit, all_units)
    if filters == 'convert_to_kg':
        price, quant, unit = convert_to_kg(
                price, quant, unit, item.item.box, all_units)
    return CustomItem(
        box_code=display.box_code,
        purchase_id=item.item.purchase_id,
        display_name=display_name,
        quantity=quant,
        price_rmb=price,
        unit=unit.name_es,
        box=item.item.box)


def generate_custom_for_purchase(dbapi, uid):
    declared = {x.uid: x for x in dbapi.search(DeclaredGood)}
    units = {x.uid: x for x in dbapi.search(Unit)}
    for item in get_purchase_item_full(dbapi, uid):
        custom = create_custom(item, declared, units)
        custom.purchase_id = uid
        custom_id = dbapi.create(custom)
        dbapi.update(item.item, {'custom_item_uid': custom_id})


@dataclasses.dataclass
class CustomItemFull(SerializableData):
    custom: CustomItem = CustomItem()
    purchase_item: List[PurchaseItemFull] = dataclasses.field(default_factory=lambda: [])



def get_custom_items_full(dbapi, uid):
    item_full = list(map(normal_filter, get_purchase_item_full(dbapi, uid)))
    items = {x.uid: CustomItemFull(x) for x in dbapi.search(CustomItem, purchase_id=uid)}
    for i in item_full:
        items[i.item.custom_item_uid].purchase_items.append(i)
    return sorted(list(items.values()), key=lambda i: i.custom.uid)



def normal_filter(item):
    item.item.price_rmb *= NORMAL_FILTER_MULT
    return item

def docen_filter(price, quantity, unit, all_units=ALL_UNITS):
    return price * 12, old_div(quantity, 12), all_units['doz']

def convert_to_kg(price, quantity, unit, box=None, all_units=ALL_UNITS):
    if unit.uid == 'kg':
        return price, quantity, unit

    # if unit converts to kg
    if unit.equiv_base == 'kg':
        mult = unit.equiv_multiplier
        return old_div(price, mult), quantity * mult, all_units['kg']

    if box is not None:
        return 0, box * 30, all_units['kg']

