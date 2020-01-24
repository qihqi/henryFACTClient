from collections import defaultdict
from decimal import Decimal
import datetime
import functools
import json
import os
import dataclasses
from henry.base.interface import SerializableInterface, DBObjectInterface
from henry.base.dbapi import dbmix, P
from henry.base.serialization import (json_dumps, parse_iso_datetime, parse_iso_date,
                                      TypedSerializableMixin)
from .schema import NInventoryRevision, NInventoryRevisionItem
from .schema import (NBodega, NCategory, NPriceListLabel,
                     NPriceList, NItemGroup, NItem, NStore, NProdTag, NProdTagContent)
from typing import Dict, Optional


@dbmix(NBodega)
@dataclasses.dataclass(init=False)
class Bodega(DBObjectInterface[NBodega], SerializableInterface):
    id: int
    nombre: str
    nivel: int

    def __init__(self, **kwargs):
        self.merge_from(kwargs)


@dbmix(NCategory)
@dataclasses.dataclass
class Category(DBObjectInterface[NCategory], SerializableInterface):
    id: int
    nombre: str

    def __init__(self, **kwargs):
        self.merge_from(kwargs)


@dbmix(NPriceListLabel)
@dataclasses.dataclass
class PriceListLabel:
    uid: int
    name: str

    def __init__(self, **kwargs):
        self.merge_from(kwargs)


@dbmix(NStore)
@dataclasses.dataclass
class Store:
    almacen_id: int
    ruc: str
    nombre: str
    bodega_id: int

    def __init__(self, **kwargs):
        self.merge_from(kwargs)


@dbmix(NProdTag)
@dataclasses.dataclass
class ProdTag:
    tag: str
    description: str
    created_by: str

    def __init__(self, **kwargs):
        self.merge_from(kwargs)


@dbmix(NProdTagContent)
@dataclasses.dataclass
class ProdTagContent:
    uid: int
    tag: str
    itemgroup_id: int

    def __init__(self, **kwargs):
        self.merge_from(kwargs)


def convert_decimal(x, default=None) -> Optional[Decimal]:
    return default if x is None else Decimal(x)


# display these names in serialized formats
_PRICE_OVERRIDE_NAME = (('prod_id', 'codigo'), ('cant_mayorista', 'threshold'))

@dbmix(NPriceList)
@dataclasses.dataclass(init=False)
class PriceList(P, DBObjectInterface[NPriceList]):
    pid: int
    nombre: str
    almacen_id: int
    prod_id: str
    # Using int for money as in number of cents.
    precio1: int
    precio2: int
    cant_mayorista: int
    upi: int
    unidad: str
    multiplicador: Decimal

    def __init__(self, **kwargs):
        self.merge_from(kwargs)

    @classmethod
    def deserialize(cls, dict_input: Dict):
        result = cls().merge_from(dict_input)
        for x, y in _PRICE_OVERRIDE_NAME:
            original = dict_input.get(y, None)
            setattr(result, x, original)
        # this is needed because deserialize does not have custom converter
        # so json parse will get float instead of decimal
        if result.multiplicador:
            result.multiplicador = Decimal(result.multiplicador)
        return result


@dbmix(NItem)
@dataclasses.dataclass(init=False)
class ProdItem(SerializableInterface, DBObjectInterface[NItem]):
    uid: int
    itemgroupid: int
    prod_id: str
    multiplier: Decimal
    unit: str

    def __init__(self, **kwargs):
        self.merge_from(kwargs)

    def merge_from(self, the_dict: Dict) -> 'ProdItem':
        super(ProdItem, self).merge_from(the_dict)
        self.multiplier = convert_decimal(self.multiplier, 1) or Decimal(1) # type: Decimal
        return self


@dbmix(NItemGroup)
@dataclasses.dataclass(init=False)
class ProdItemGroup:
    uid: int
    prod_id: str
    name: str
    desc: str
    base_unit: str
    base_price_usd: Decimal

    def __init__(self, **kwargs):
        self.merge_from(kwargs)

    def merge_from(self, the_dict):
        fieldcopy(self, the_dict)
        self.base_price_usd = convert_decimal(self.base_price_usd, 0)
        return self


def get_real_prod_id(uid):
    if uid[-1] in ('+', '-'):
        return uid[:-1]
    return uid


def make_itemgroup_from_pricelist(pl: PriceList) -> ProdItemGroup:
    ig = ProdItemGroup(
        prod_id=get_real_prod_id(pl.prod_id),
        name=get_real_prod_id(pl.nombre))
    if pl.multiplicador == 1:
        ig.base_unit = pl.unidad
        ig.base_price_usd = Decimal(pl.precio1) / 100
    return ig


def make_item_from_pricelist(pl: PriceList) -> ProdItem:
    i = ProdItem(
        prod_id=pl.prod_id,
        multiplier=pl.multiplicador,
        unit=pl.unidad)
    return i


def create_items_chain(dbapi, pl):
    prod_id = get_real_prod_id(pl.prod_id)
    ig = dbapi.getone(ProdItemGroup, prod_id=prod_id)
    if ig is None:
        ig = make_itemgroup_from_pricelist(pl)
        dbapi.create(ig)
    item = dbapi.getone(ProdItem, prod_id=pl.prod_id)
    if item is None:
        item = make_item_from_pricelist(pl)
        item.itemgroupid = ig.uid
        dbapi.create(item)
    pricelist = dbapi.getone(PriceList, prod_id=pl.prod_id, almacen_id=pl.almacen_id)
    if pricelist is None:
        pricelist = PriceList()
        pricelist.merge_from(pl)
        dbapi.create(pricelist)


class RevisionApi(object):
    AJUSTADO = 'AJUSTADO'
    NUEVO = 'NUEVO'
    CONTADO = 'CONTADO'

    def __init__(self, sessionmanager, countapi, transactionapi):
        self.sm = sessionmanager
        self.countapi = countapi
        self.transactionapi = transactionapi

    def save(self, bodega_id, user_id, items):
        session = self.sm.session
        revision = NInventoryRevision()
        revision.bodega_id = bodega_id
        revision.timestamp = datetime.datetime.now()
        revision.created_by = user_id
        revision.status = self.NUEVO
        for prod_id in items:
            item = NInventoryRevisionItem(prod_id=prod_id)
            revision.items.append(item)
        session.add(revision)
        session.flush()
        return revision

    def get(self, rid):
        return self.sm.session.query(
            NInventoryRevision).filter_by(uid=rid).first()

    def update_count(self, rid, items_counts):
        revision = self.get(rid)
        if revision is None:
            return None
        for item in revision.items:
            prod = self.countapi.getone(prod_id=item.prod_id,
                                        bodega_id=revision.bodega_id)
            item.inv_cant = prod.cant
            item.real_cant = items_counts[item.prod_id]

        revision.status = self.CONTADO
        self.sm.session.flush()
        return revision

    def commit(self, rid):
        revision = self.get(rid)
        if revision is None:
            return None
        if revision.status != 'CONTADO':
            return revision
        reason = 'Revision: codigo {}'.format(rid)
        now = datetime.datetime.now()
        bodega_id = revision.bodega_id
        for item in revision.items:
            pass
        #           TODO: use inventory api
        #            delta = item.real_cant - item.inv_cant
        #            transaction = Transaction(
        #                upi=None,
        #                bodega_id=bodega_id,
        #                prod_id=item.prod_id,
        #                delta=delta,
        #                ref=reason,
        #                fecha=now)
        #            self.transactionapi.save(transaction)
        revision.status = 'AJUSTADO'
        return revision


def quantity_tuple(quantities):
    # quantities should be a list of tuples of bodega_id: quantity
    # with type (int, Decimal)
    # the starting type is (int, str), need to convert str to decimal
    return [(x[0], Decimal(x[1])) for x in quantities]


#  saves the item stock count at a given time
class InventorySnapshot(TypedSerializableMixin):
    """
    quantity is a list of tuples (bodega_id, quantity)
    """
    _fields = (
        ('creation_time', parse_iso_datetime),
        ('itemgroup_id', int),
        ('prod_id', str),
        ('quantity', quantity_tuple),
        ('upto_date', parse_iso_date),
        ('last_upto_date', parse_iso_date),
        ('last_quantity', quantity_tuple))


class InvMovementType(object):
    SALE = 'sale'
    TRANSFER = 'transfer'
    INGRESS = 'ingress'
    EGRESS = 'egress'
    DELETE_SALE = 'delete_sale'
    DELETE_TRANFER = 'delete_tranfer'
    DELETE_INGRESS = 'delete_ingress'
    DELETE_EGRESS = 'delete_egress'
    INITIAL = 'initial_stock'

    @classmethod
    def delete_type(cls, type_):
        return 'delete_' + type_


#  tracks every movement of inventory
class InventoryMovement(TypedSerializableMixin):
    """
        should have following attributes:
        from_inv_id: (int) id of from bodega
        to_inv_id: (int) id of to bodega
        quantity: (Decimal) positive quantity
        itemgroup: (ProdItemGroup) item in movement
        timestamp: (datetime) time of execution
        type: (str) one of InvMovementType
    """
    _fields = (
        ('from_inv_id', int),
        ('to_inv_id', int),
        ('quantity', Decimal),
        ('itemgroup_id', int),
        ('prod_id', str),
        ('timestamp', parse_iso_datetime),
        ('type', str),
        ('reference_id', str),
    )

    def inverse(self):
        self.from_inv_id, self.to_inv_id = self.to_inv_id, self.from_inv_id
        return self


class InventoryApi(object):
    SNAPSHOT_FILE_NAME = '__snapshot'

    def __init__(self, fileservice):
        self.fileservice = fileservice

    @classmethod
    def _year_month(cls, date):
        return '{:04d}-{:02d}'.format(date.year, date.month)

    @classmethod
    def _make_filename(cls, igid, date):
        # PROD_ID/yyyy-mm
        return os.path.join(str(igid), cls._year_month(date))

    def save(self, inv_movement):
        path = InventoryApi._make_filename(
            inv_movement.itemgroup_id, inv_movement.timestamp.date())
        self.fileservice.append_file(path, json_dumps(inv_movement))

    def bulk_save(self, trans):
        for t in trans:
            self.save(t)

    def get_past_records(self, igid):
        snapshotname = os.path.join(str(igid), self.SNAPSHOT_FILE_NAME)
        snapshot_path = self.fileservice.make_fullpath(snapshotname)
        if os.path.exists(snapshot_path):
            records = self.fileservice.get_file(snapshotname)
            return list(map(InventorySnapshot.deserialize, json.loads(records)))
        return []

    def list_transactions(self, igid, start_date, end_date):
        # start date can be None, but end_date cannot
        if not isinstance(end_date, datetime.date):
            raise ValueError('end_date must be a valid date object')
        if not isinstance(start_date, datetime.date) and start_date is not None:
            raise ValueError('start_date must be a valid date object')
        root = self.fileservice.make_fullpath(str(igid))
        last_month = InventoryApi._year_month(end_date)
        all_fname = [f for f in os.listdir(root) if f <= last_month]
        if all_fname:
            if start_date is None:
                smallest = min(all_fname)
                year, month = list(map(int, smallest.split('-')))
                start_date = datetime.date(year, month, 1)
            all_fname = [f for f in all_fname if
                         f >= InventoryApi._year_month(start_date)]
            all_fname = list(map(functools.partial(os.path.join, str(igid)), all_fname))
            for x in self.fileservice.get_file_lines(all_fname):
                item = InventoryMovement.deserialize(json.loads(x))
                if start_date <= item.timestamp.date() <= end_date:
                    yield item

    def get_changes(self, igid, start_date, end_date):
        deltas = defaultdict(Decimal)
        for x in self.list_transactions(igid, start_date, end_date):
            if x.from_inv_id is not None:
                deltas[x.from_inv_id] -= x.quantity
            if x.to_inv_id is not None:
                deltas[x.to_inv_id] += x.quantity
        return deltas

    def _write_snapshot(self, igid, records):
        snapshotname = os.path.join(str(igid), self.SNAPSHOT_FILE_NAME)
        self.fileservice.put_file(snapshotname, json_dumps(records))

    def take_snapshot_to_date(self, igid, end_date):
        new_record, records = self._get_new_snapshot_to_date(igid, end_date)
        records.insert(0, new_record)
        self._write_snapshot(igid, records[:-1])

    def _get_new_snapshot_to_date(self, igid, end_date):
        # get last account
        records = self.get_past_records(igid)
        start_date = None
        if records:
            # starting date is one day after lasttime!
            start_date = records[0].upto_date + datetime.timedelta(days=1)

        deltas = self.get_changes(igid, start_date, end_date)
        last_quantities = self._get_last_snapshot_quantities(records)

        new_quantities = {}
        for inv_id in set(deltas.keys()) | set(last_quantities.keys()):
            new_quantities[inv_id] = deltas[inv_id] + last_quantities[inv_id]

        new_record = InventorySnapshot()
        new_record.upto_date = end_date
        new_record.creation_date = datetime.datetime.now()
        new_record.quantity = list(new_quantities.items())
        new_record.last_quantity = list(last_quantities.items())
        new_record.last_upto_date = start_date

        return new_record, records

    def _get_last_snapshot_quantities(self, records):
        last_quantities = defaultdict(Decimal)
        if records:
            for inv_id, quantity in records[0].quantity:
                last_quantities[inv_id] = quantity
        return last_quantities

    def get_current_quantity(self, igid):
        new_record, _ = self._get_new_snapshot_to_date(igid, datetime.date.today())
        return defaultdict(Decimal, new_record.quantity)
