import datetime
from collections import defaultdict
from operator import attrgetter

from bottle import request, Bottle, response
from henry.dao import Status
from henry.reports import split_records
from henry.base.schema import NUsuario
from henry.config import sessionmanager, jinja_env, dbcontext, fix_id, prodapi, invapi

w = Bottle()
accounting_webapp = w


class CustomerSell(object):
    def __init__(self):
        self.subtotal = 0
        self.iva = 0
        self.count = 0
        self.total = 0


def get_all_users():
    with sessionmanager as session:
        all_user = session.query(NUsuario).all()
    return all_user


def group_by_customer(inv):
    result = defaultdict(CustomerSell)
    for i in inv:
        cliente_id = fix_id(i.client.codigo)
        disc = i.discount if i.discount else 0
        result[cliente_id].subtotal += (i.subtotal - disc)
        result[cliente_id].iva += i.tax
        result[cliente_id].total += i.total
        result[cliente_id].count += 1
    return result


@w.get('/app/accounting_form')
@dbcontext
def get_sells_xml_form():
    temp = jinja_env.get_template('ats_form.html')
    stores = filter(lambda x: x.ruc, prodapi.get_stores())
    return temp.render(stores=stores, title='ATS')


class Meta(object):
    pass


@w.get('/app/accounting.xml')
@dbcontext
def get_sells_xml():
    datestrp = datetime.datetime.strptime
    start_date = datestrp(request.query.get('start_date'), "%Y-%m-%d")
    end_date = datestrp(request.query.get('end_date'), "%Y-%m-%d")
    form_type =  request.query.get('form_type')

    ruc = request.query.get('alm')
    invs = invapi.search_metadata_by_date_range(
        start_date, end_date, other_filters={'almacen_ruc': ruc})
    by_status = split_records(invs, attrgetter('status'))
    sold = by_status[Status.COMITTED] + by_status[Status.NEW]
    grouped = group_by_customer(sold)
    deleted = by_status[Status.DELETED]

    meta = Meta()
    meta.date = start_date
    meta.total = reduce(lambda acc, x: acc + x.total, grouped.values(), 0)
    meta.almacen_ruc = ruc
    meta.almacen_name = [x.nombre for x in prodapi.get_stores() if x.ruc == ruc][0]
    temp = jinja_env.get_template('resumen_agrupado.html')
    if form_type == 'ats':
        temp = jinja_env.get_template('ats.xml')
        response.set_header('Content-disposition', 'attachment')
        response.set_header('Content-type', 'application/xml')
    return temp.render(vendidos=grouped, eliminados=deleted, meta=meta)

