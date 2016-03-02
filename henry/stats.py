from henry.accounting.reports import *
from henry.config import *

session = sessionmanager.__enter__()


def full_invoice_items(start_date, end_date):
    invs = invapi.search_metadata_by_date_range(start_date, end_date)
    for inv in invs:
        fullinv = invapi.get_doc_from_file(inv.items_location)
        if fullinv is None:
            continue
        for x in fullinv.items:
            yield inv, x

def sale_by_date(date, almacen_id):
    start = date
    end = start + datetime.timedelta(days=1)
    prods_sale = defaultdict(Item)
    for inv, x in full_invoice_items(start, end):
        if inv.almacen_id != almacen_id:
            continue
        obj = prods_sale[x.prod.codigo]
        obj.prod = x.prod
        if obj.cant:
            obj.cant += x.cant
        else:
            obj.cant = x.cant
    return prods_sale


def sorton(prods_sale, cant=True):
    if cant:
        key = lambda x: x.cant
    else:
        key = lambda x: x.cant * x.prod.precio1
    return sorted(prods_sale, key=key)


def display_prod_sale(prods_sale):
    for x in prods_sale:
        print '{}\t{}\t{}\t{}\t{}'.format(
            x.prod.codigo,
            x.prod.nombre,
            x.prod.cant,
            x.prod.precio1 * x.cant)
today = datetime.datetime.now()
yesterday = today - datetime.timedelta(days=1)
twodays = today - datetime.timedelta(days=2)

last_week_alm = [sorton(sale_by_date(d, 1).values()) for d in (today, yesterday, twodays)]
