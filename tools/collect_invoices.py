from collections import defaultdict
from datetime import date, datetime, time, timedelta
import os
from henry.base.serialization import json_dumps

from henry.coreconfig import sessionmanager, invapi, clientapi
from henry.config import prodapi
from henry.product.schema import NProducto
from henry.schema.legacy import NOrdenDespacho, NItemDespacho
from henry.dao.document import Item, Status
from henry.dao.productos import Product
from henry.dao.order import Invoice, InvMetadata
from henry.invoice.dao import PaymentFormat, InvMetadata, Invoice


# old OrdenDespacho
def query_all_fully_joined(session, start, end):
    s = session.query(NOrdenDespacho, NItemDespacho, NProducto).filter(
        NOrdenDespacho.id == NItemDespacho.desp_cod_id).filter(
        NItemDespacho.producto_id == NProducto.codigo).filter(
        NOrdenDespacho.fecha >= start).filter(
        NOrdenDespacho.fecha <= end)
    return s

def money_to_cent(money):
    return int(money * 100)


def newpayformat(oldformat):
    format_dict = {
        'E': PaymentFormat.CASH,
        'C': PaymentFormat.CHECK,
        'T': PaymentFormat.CARD,
        'D': PaymentFormat.DEPOSIT,
        'R': PaymentFormat.CREDIT,
        'V': PaymentFormat.VARIOUS,
    }
    return format_dict[oldformat.upper()]

def get_all_client():
    cliente = {}
    for x in clientapi.search():
        cliente[x.codigo] = x
    return cliente


def old_to_new_invoice(old_inv, all_client):
    meta_item = defaultdict(list)
    for meta, item, prod in old_inv:
        meta_item[meta.id].append((meta, item, prod))

    print 'total record', len(meta_item)
    for m, i in meta_item.items():
        m = i[0][0]
        almacen_id = m.bodega_id
        codigo = m.codigo
        if codigo < 0:
            codigo = abs(codigo)
            almacen_id = 3

        tax_percent = 12 if almacen_id != 2 else 0

        store = prodapi.store.get(almacen_id)
        meta = InvMetadata(
            almacen_id=almacen_id,
            almacen_name=store.nombre,
            almacen_ruc=store.ruc,
            codigo=str(codigo),
            user=m.vendedor_id,
            client=all_client[m.cliente_id],
            timestamp=datetime.combine(m.fecha, time(1, 0, 0)),
            payment_format=newpayformat(m.pago),
            total=money_to_cent(m.total),
            tax_percent=tax_percent,
        )
        meta.status = Status.DELETED if m.eliminado else Status.COMITTED
        meta.subtotal = int(meta.total / (1 + tax_percent/100.0))
        meta.tax = meta.total - meta.subtotal

        def make_item(ix):
            p = Product().merge_from(ix[2])
            p.precio1 = money_to_cent(ix[1].precio)
            return Item(p, ix[1].cantidad)
        items = map(make_item, i)
        inv = Invoice(meta, items)
        yield inv

def save_inv(content, ddate, directory, prefix):
    fname = '{}-{}.txt'.format(prefix, ddate.isoformat())
    fullpath = os.path.join(directory, fname)
    with open(fullpath, 'w') as f:
        for x in content:
            f.write(json_dumps(x.serialize()))
            f.write('\n')


def query_and_save_old_invoices(session, start_date, end_date, directory, prefix):
    all_client = get_all_client()
    all_items = query_all_fully_joined(
        session, start_date, end_date)
    by_date = []
    start_date = None
    for inv in sorted(old_to_new_invoice(all_items, all_client), key=lambda x: x.meta.timestamp):
        curtime = inv.meta.timestamp.date()
        if start_date is None:
            start_date = curtime
        if curtime == start_date:
            by_date.append(inv)
        else:
            save_inv(by_date, start_date, directory, prefix)
            by_date = []
            start_date = curtime


DIRECTORY = './invold'
PREFIX = 'inv'
def main():
    curdate=date(2012,1,1)
    enddate=date(2015,9,1)
    delta = timedelta(days=30)
    with sessionmanager as session:
        while curdate < enddate:
            query_and_save_old_invoices(session, curdate, curdate + delta, DIRECTORY, PREFIX)
            print 'saved for', curdate
            curdate += delta


main()
