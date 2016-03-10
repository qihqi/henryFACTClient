import datetime
from decimal import Decimal

from bottle import abort

from henry.base.common import parse_iso
from henry.inventory.dao import TransMetadata, TransType, TransItem
from henry.product.dao import PriceList, ProdItemGroup


def get_base_price(dbapi, prod_id):
    plus = prod_id + '+'
    price = dbapi.search(PriceList, prod_id=plus, almacen_id=2)
    if not price:
        price = dbapi.search(PriceList, prod_id=prod_id, almacen_id=2)
    if not price:
        return None
    price = price[0]
    mult = price.multiplicador or 1
    return Decimal(price.precio1) / 100 / mult


def items_from_form(dbapi, form):
    items = []
    for cant, prod_id in zip(
            form.getlist('cant'),
            form.getlist('codigo')):
        if not cant.strip() or not prod_id.strip():
            # skip empty lines
            continue
        try:
            cant = Decimal(cant)
        except ValueError:
            abort(400, 'cantidad debe ser entero positivo')
        if cant < 0:
            abort(400, 'cantidad debe ser entero positivo')
        itemg = dbapi.getone(ProdItemGroup, prod_id=prod_id)
        items.append(TransItem(itemg, cant))
    return items


def transmetadata_from_form(form):
    meta = TransMetadata()
    meta.dest = form.get('dest')
    meta.origin = form.get('origin')
    fecha = form.get('fecha')
    if fecha:
        fecha = parse_iso(fecha)
        meta.timestamp = datetime.datetime.combine(
            fecha.date(), datetime.datetime.now().time())
    try:
        meta.dest = int(meta.dest)
        meta.origin = int(meta.origin)
    except ValueError:
        pass
    meta.meta_type = form.get('meta_type')
    meta.trans_type = form.get('trans_type')
    if meta.trans_type == TransType.INGRESS:
        meta.origin = None  # ingress does not have origin
    if meta.trans_type in (TransType.EXTERNAL or TransType.EGRESS):
        meta.dest = None  # dest for external resides in other server
    if meta.timestamp is None:
        meta.timestamp = datetime.datetime.now()
    return meta


