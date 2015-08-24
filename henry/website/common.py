import datetime
from decimal import Decimal

from bottle import abort

from henry.config import itemgroupapi, prodapi
from henry.dao.inventory import TransMetadata, TransType, TransItem
from henry.dao.productos import ProdItemGroup


def get_base_price(prod_id):
    plus = prod_id + '+'
    price = prodapi.price.search(prod_id=plus, almacen_id=2)
    if not price:
        price = prodapi.price.search(prod_id=prod_id, almacen_id=2)
    if not price:
        return None
    price = price[0]
    mult = price.multiplicador or 1
    return Decimal(price.precio1) / 100 / mult

def parse_iso(date_string):
    return datetime.datetime.strptime(date_string, '%Y-%m-%d')


def parse_start_end_date(forms, start_name='start', end_name='end'):
    start = forms.get(start_name, None)
    end = forms.get(end_name, None)
    try:
        if start:
            start = parse_iso(start)
        else:
            start = None
        if end:
            end = parse_iso(end)
        else:
            end = None
    except:
        abort(400, 'Fecha en formato equivocada')
    return start, end


def items_from_form(form):
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
        itemg_list = itemgroupapi.search(prod_id=prod_id)
        if not itemg_list:
            #  this item does not exist. Probably it was never backfilled
            prod = prodapi.prod.get(prod_id)
            baseprice = get_base_price(prod_id)
            itemg = ProdItemGroup(
                name=prod.nombre,
                prod_id=prod.codigo,
                base_price_usd=baseprice)
            itemgroupapi.create(itemg)
        else:
            itemg = itemg_list[0]
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


def convert_to_cent(dec):
    if not isinstance(dec, Decimal):
        dec = Decimal(dec)
    return int(dec * 100)


def parse_start_end_date_with_default(form, start, end):
    newstart, newend = parse_start_end_date(form)
    if newend is None:
        newend = end
    if newstart is None:
        newstart = start
    if isinstance(newstart, datetime.datetime):
        newstart = newstart.date()
    if isinstance(newend, datetime.datetime):
        newend = newend.date()
    return newstart, newend
