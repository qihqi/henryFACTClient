import datetime
from decimal import Decimal

from bottle import abort

from henry.config import prodapi
from henry.dao import Item, TransMetadata, TransType


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
        items.append(Item(prodapi.get_producto(prod_id), cant))
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
