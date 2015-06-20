from datetime import datetime, date, time
from collections import defaultdict
from datetime import date
from henry.config import sessionmanager, invapi
from henry.base.schema import NItemDespacho, NOrdenDespacho, NCliente, NProducto
from henry.dao import InvMetadata, Client, PaymentFormat, Item, Product, Invoice, Status


def query_all_fully_joined(session, start, end):
    s = session.query(NOrdenDespacho, NItemDespacho).filter(
        NOrdenDespacho.id == NItemDespacho.desp_cod_id).filter(
        NOrdenDespacho.fecha >= start).filter(
        NOrdenDespacho.fecha <= end).filter_by(bodega_id=1)
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

def get_all_client(session):
    cliente = {}
    for x in session.query(Client):
        cliente[x.codigo] = x
    return cliente


def get_all_prod(session):
    prod = {}
    for x in session.query(NProducto):
        prod[x.codigo.upper()] = Product().merge_from(x)
    return prod

def main():
    with sessionmanager as session:

        all_client = get_all_client(session)
        prods = get_all_prod(session)
        meta_item = defaultdict(list)
        for meta, item in query_all_fully_joined(session, date(2014, 12, 1), date(2014, 12, 2)):
            meta_item[meta].append(item)
        for m, i in meta_item.items():
            meta = InvMetadata(
                almacen_id=1,
                codigo=str(m.codigo),
                user=m.vendedor_id,
                client=all_client[m.cliente_id],
                timestamp=datetime.combine(m.fecha, time()),
                payment_format=newpayformat(m.pago),
                total=money_to_cent(m.total),
                tax_percent=12,
            )
            meta.status = Status.DELETED if m.eliminado else Status.COMITTED
            meta.subtotal = int(meta.total / 1.12)
            meta.tax = meta.total - meta.subtotal

            def make_item(ix):
                p = prods[ix.producto_id.upper()]
                p.precio1 = money_to_cent(ix.precio)
                return Item(p, ix.cantidad)
            items = map(make_item, i)

            inv = Invoice(meta, items)
            invapi.save(inv)
    print len(meta_item)
    print 'end'
main()
