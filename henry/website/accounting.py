import datetime
from decimal import Decimal, ROUND_HALF_DOWN
from collections import defaultdict

from bottle import request, Bottle, response
from henry.layer2.documents import Status
from henry.layer1.schema import NUsuario
from henry.config import sessionmanager, jinja_env, invapi2

w = Bottle()
accounting_webapp = w


class CustomerSell(object):

    def __init__(self):
        self.subtotal = 0
        self.iva = 0
        self.count = 0


def get_all_users():
    with sessionmanager as session:
        all_user = session.query(NUsuario).all()
    return all_user


def extract_vta_from_total(total):
    return (total / Decimal('1.12')).quantize(Decimal('.01'),
                                              rounding=ROUND_HALF_DOWN)


def group_by_customer(inv):
    result = defaultdict(CustomerSell)
    for i in inv:
        vta = extract_vta_from_total(i.total)
        subtotal = i.total - vta
        result[i.cliente_id].subtotal += subtotal
        result[i.cliente_id].iva += vta
        result[i.cliente_id].count += 1
    return result


@w.get('/app/accounting_form')
def get_sells_xml_form():
    temp = jinja_env.get_template('ats_form.html')
    return temp.render(today=datetime.date.today(), vendedores=get_all_users())


class Meta(object):
    pass


@w.get('/app/accounting.xml')
def get_sells_xml():
    datestrp = datetime.datetime.strptime
    start_date = datestrp(request.query.get('start_date'), "%Y-%m-%d")
    end_date = datestrp(request.query.get('end_date'), "%Y-%m-%d")

    seller = request.query.get('vendido')
    sold = invapi2.get_dated_report(
        start_date, end_date, 1, seller=seller, status=Status.COMITTED)
    grouped = group_by_customer(sold)
    deleted = invapi2.get_dated_report(
        start_date, end_date, 1, seller=seller, status=Status.DELETED)

    meta = Meta()
    meta.date = start_date
    meta.total = reduce(lambda acc, x: acc + x.subtotal, sold.values(), 0)
    temp = jinja_env.get_template('ats.xml')
    # response.set_header('Content-disposition', 'attachment')
    response.set_header('Content-type', 'application/xml')
    return temp.render(vendidos=grouped, eliminados=deleted, meta=meta)
