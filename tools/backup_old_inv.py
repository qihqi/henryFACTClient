from datetime import datetime, date, time
from collections import defaultdict
from datetime import date
from henry.config import sessionmanager, invapi, prodapi
from henry.schema.inventory import NProducto
from henry.schema.core import NNota, NCliente
from henry.schema.legacy import NOrdenDespacho, NItemDespacho
from henry.dao import InvMetadata, Client, PaymentFormat, Item, Product, Invoice, Status


def query_all_fully_joined(session, start, end, bodega_id):
    s = session.query(NOrdenDespacho, NItemDespacho, NProducto).filter(
        NOrdenDespacho.id == NItemDespacho.desp_cod_id).filter(
        NItemDespacho.producto_id == NProducto.codigo).filter(
        NOrdenDespacho.fecha >= start).filter(
        NOrdenDespacho.fecha <= end).filter_by(bodega_id=bodega_id)
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

def main():
    with sessionmanager as session:

        all_client = get_all_client(session)
        meta_item = defaultdict(list)
        bodega_id = 1
        tax_percent = 12
        for meta, item, prod in query_all_fully_joined(
                session,
                date(2015, 6, 1), date(2015, 7, 4), bodega_id):
            meta_item[meta].append((item, prod))
        for m, i in meta_item.items():
            almacen_id = bodega_id
            codigo = m.codigo
            if codigo < 0:
                codigo = abs(codigo)
                almacen_id = 3
            existing = session.query(NNota).filter_by(almacen_id=almacen_id, codigo=codigo).first()
            if existing is not None:
                print 'codigo {} en bodega {} ya existe, pasando'.format(m.codigo, bodega_id)
                continue

            store = prodapi.get_store_by_id(almacen_id)
            meta = InvMetadata(
                almacen_id=almacen_id,
                almacen_name=store.nombre,
                almacen_ruc=store.ruc,
                codigo=str(codigo),
                user=m.vendedor_id,
                client=all_client[m.cliente_id],
                timestamp=datetime.combine(m.fecha, time()),
                payment_format=newpayformat(m.pago),
                total=money_to_cent(m.total),
                tax_percent=tax_percent,
            )
            meta.status = Status.DELETED if m.eliminado else Status.COMITTED
            meta.subtotal = int(meta.total / (1 + tax_percent/100.0))
            meta.tax = meta.total - meta.subtotal

            def make_item(ix):
                p = Product().merge_from(ix[1])
                p.precio1 = money_to_cent(ix[0].precio)
                return Item(p, ix[0].cantidad)
            items = map(make_item, i)

            inv = Invoice(meta, items)
            invapi.save(inv)
    print len(meta_item)
    print 'end'
main()
