import sys
from datetime import date
from henry.config import sessionmanager, prodapi
from henry.base.schema import (NIngreso, NIngresoItem, NOrdenDespacho,
    NItemDespacho, NContenido, NTransform)
from collections import defaultdict
from decimal import Decimal

child_price_map = {}
parent_to_child_map = {}

def fill_map(session):
    for x in session.query(NContenido):
        child_price_map[x.prod_id.upper()] = x.precio
    for x in session.query(NTransform):
        parent_to_child_map[x.origin_id.upper()] = (x.dest_id, x.multiplier)


def getprice(prod_id):
    prod_id = prod_id.upper()
    if prod_id in child_price_map:
        return child_price_map[prod_id]
    if prod_id in parent_to_child_map:
        child, mult = parent_to_child_map[prod_id]
        child = child.upper()
        if child in child_price_map:
            return mult * child_price_map[child]
    return 0


def main():
    ing_per_week = defaultdict(Decimal)
    sale_per_week = defaultdict(Decimal)
    ing_by_prod = defaultdict(Decimal)
    sale_by_prod = defaultdict(Decimal)

    ing_prod_not_found = set()
    sale_prod_not_found = set()
    start, end = date(2014, 1, 1), date(2015, 12, 31)
    with sessionmanager as session:
        fill_map(session)
        all_ingreso_item = session.query(
            NIngreso.id, NIngreso.fecha, NIngresoItem.cantidad,
            NIngresoItem.producto_id).filter(NIngreso.id==NIngresoItem.ref_id,
            NIngreso.tipo == 'E', NIngreso.fecha >= start,
            NIngreso.fecha <= end)

        for item in all_ingreso_item:
            weekid = '{:04d}-{:02d}'.format(item.fecha.isocalendar()[0],
                                    item.fecha.isocalendar()[1])
            item_value = item.cantidad * getprice(item.producto_id)
            ing_per_week[weekid] += item_value
            prodid = item.producto_id.upper()
            if item_value == 0:
                ing_prod_not_found.add(prodid)
            else:
                if prodid in parent_to_child_map:
                    child, mult = parent_to_child_map[prodid]
                    ing_by_prod[child] += item.cantidad * mult
                else:
                    ing_by_prod[prodid] += item.cantidad

        all_sale_item = session.query(
            NItemDespacho.cantidad, NItemDespacho.producto_id, NOrdenDespacho.fecha,
            NOrdenDespacho.id).filter(NOrdenDespacho.id==NItemDespacho.desp_cod_id,
            NOrdenDespacho.fecha >= start, NOrdenDespacho.fecha <= end)

        for item in all_sale_item:
            weekid = '{:04d}-{:02d}'.format(item.fecha.isocalendar()[0],
                                    item.fecha.isocalendar()[1])
            item_value = item.cantidad * getprice(item.producto_id)
            sale_per_week[weekid] += item_value
            prodid = item.producto_id.upper()
            if item_value == 0:
                sale_prod_not_found.add(prodid)
            else:
                sale_by_prod[item.producto_id.upper()] += item.cantidad

    #for key, value in sale_per_week.items():
    #    print '{}\t{}\t{}'.format(key, value, ing_per_week[key])
    for key, value in sale_by_prod.items():
        print '{}\t{}\t{}\t{}'.format(prodapi.get_producto(key).nombre, key, value, ing_by_prod[key])
    print >>sys.stderr, sum(sale_per_week.values()), sum(ing_per_week.values())
    print >>sys.stderr, 'sale not found', len(sale_prod_not_found), sale_prod_not_found
    print >>sys.stderr, 'ing not found', len(ing_prod_not_found), ing_prod_not_found
main()
