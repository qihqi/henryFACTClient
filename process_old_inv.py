from collections import defaultdict
import datetime
import os
import json
import matplotlib.pyplot as plt
from decimal import Decimal
from henry.coreconfig import sessionmanager
from henry.dao.document import Status, Item
from henry.dao.inventory import Transferencia

from henry.dao.order import Invoice
from henry.product.schema import NPriceList

DIR = './invold'


def iterate_date(start, end):
    delta = datetime.timedelta(days=1)
    while start <= end:
        yield start
        start += delta

def open_and_iterate_file(fname):
    if not os.path.exists(fname):
        return None
    with open(fname) as f:
        return map(json.loads, f.xreadlines())


def stream_inv(prefix, start_date, end_date):
    for x in stream_obj('inv', start_date, end_date, Invoice):
        yield x
    for x in stream_obj('sale', start_date, end_date, Invoice):
        yield x


def stream_obj(prefix, start_date, end_date, clazz):
    for thedate in iterate_date(start_date, end_date):
        fname = os.path.join(DIR, '{}-{}.txt'.format(prefix, thedate.isoformat()))
        resultset = open_and_iterate_file(fname)
        if resultset is not None:
            for x in resultset:
                yield clazz.deserialize(x)


def stream_trans(prefix, start_date, end_date):
    for x in stream_obj(prefix, start_date, end_date, Transferencia):
        yield x



def make_bar_graph(list_of_pairs):
    x_value = [x[0] for x in list_of_pairs]
    y_value = [x[1] for x in list_of_pairs]
    start = list_of_pairs[0][0]
    
    pos = [(x - start).days for x in x_value]
    
    fig, ax = plt.subplots()
    bar = ax.bar(pos, y_value, 0.3, color='r')
    plt.show()

def make_graph(list_of_pairs):

    for x, y in list_of_pairs:
        print x.isoweekday(), x.isoformat(),
        print '=' * (y / 50000)

def histogram(values):
    plt.hist(values, bins=50000)
    plt.show()

def get_trans_val(i, pricelist):
    total = 0
    for x in i.items:
        if x.prod.base_price_usd is None:
            x.prod.base_price_usd = Decimal(pricelist.get(x.prod.prod_id, 0)) / 100
        total += x.cant * (x.prod.base_price_usd or 0)
    return total


def make_pricelist(session):
    plist = {}
    for x in session.query(NPriceList).filter_by(almacen_id=2):
        plist[x.prod_id] = x.precio1
    return plist


def main():
    start_date = datetime.date(2015, 1, 1)
    end_date = datetime.date(2016, 1, 1)

    sales_by_week = defaultdict(Decimal)
    transfer_by_week = defaultdict(Decimal)

    with sessionmanager as session:
        pricelist = make_pricelist(session)

    for i in stream_inv('sale', start_date, end_date):
        if i.meta.status != Status.COMITTED:
            continue
        if i.meta.almacen_id == 2:
            continue
        key = tuple(i.meta.timestamp.isocalendar()[:2])
        sales_by_week[key] += Decimal(i.meta.total) / 100

    for i in stream_trans('trans', start_date, end_date):
        if i.meta.status == Status.DELETED:
            continue
        if i.meta.dest != 1:
            continue
        key = tuple(i.meta.timestamp.isocalendar()[:2])
        transfer_by_week[key] += get_trans_val(i, pricelist)

    for x, y in sorted(sales_by_week.items()):
        print x[0], ',', x[1], ',', y, ',', transfer_by_week.get(x, 0)



if __name__ == '__main__':
    main()

