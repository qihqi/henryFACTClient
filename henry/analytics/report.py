from collections import defaultdict
from decimal import Decimal

from operator import itemgetter
import os
from henry.base.serialization import json_loads
from henry.invoice.dao import Invoice
from .exporting import dump_content


class SaleItem(object):

    def __init__(self, item):
        self.item = item

    @property
    def uid(self):
        return self.item.prod.prod_id

    @property
    def price(self):
        return self.item.prod.precio1

    @property
    def cant(self):
        return self.item.cant


class SaleTransaction(object):

    def __init__(self, sale):
        self.sale = sale

    @property
    def type(self):
        return 'Invoice'

    @property
    def uid(self):
        return self.sale.meta.uid

    @property
    def value(self):
        return self.sale.meta.total - (self.sale.meta.tax or 0)

    @property
    def items(self):
        return map(SaleItem, self.sale.items)


class TransItem(object):

    def __init__(self, item):
        self.item = item

    @property
    def uid(self):
        return self.item.prod.prod_id

    @property
    def price(self):
        return int(self.item.prod.base_price_usd * 100)

    @property
    def cant(self):
        return self.item.cant


def get_type(prod_id):
    return prod_id


class DailyReport(object):

    def __init__(self, date, raw_inv):
        self._raw_inv = raw_inv
        self.date = date
        self.by_type = defaultdict(Decimal)
        self.by_type_count = defaultdict(int)
        self.by_prod = defaultdict(Decimal)
        self.by_prod_count = defaultdict(int)
        self.total_value = 0
        self.total_count = 0

    def process(self):
        self.by_type = defaultdict(int)
        self.by_type_count = defaultdict(int)
        self.by_prod = defaultdict(int)
        self.by_prod_count = defaultdict(int)
        self.total_value = 0
        self.total_count = 0
        for inv in self._raw_inv:
            for i in inv.items:
                val = old_div(i.cant * i.price, 100)
                self.by_type[get_type(i.uid)] += val
                self.by_type_count[get_type(i.uid)] += 1
                self.by_prod[i.uid] += val
                self.by_prod_count[i.uid] += 1
            self.total_value += inv.value
            self.total_count += 1


class ExportManager(object):

    def __init__(self, store_dir, prefix, baseurl):
        self.store_dir = store_dir
        self.baseurl = baseurl
        self.prefix = prefix

    def decode_iter(self, content):
        def d_(line):
            j = json_loads(line)
            return Invoice.deserialize(j)
        raw = map(d_, content)
        return raw

    def get(self, day):
        fname = '{}-{}.txt'.format(self.prefix, day.isoformat())
        fname = os.path.join(self.store_dir, fname)
        if not os.path.exists(fname):
            return None
        with open(fname) as f:
            content = self.decode_iter(f)
            result = DailyReport(day, content)
            result.process()
            return result

    def reload_analytics(self, day):
        invurl = self.baseurl + '/api/nota'
        invurllist = self.baseurl + '/app/api/nota'
        dump_content(day, self.store_dir, self.prefix, invurllist, invurl)
        return True


if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as f:
        def decode(line):
            j = json_loads(line)
            return Invoice.deserialize(j)
        raw = map(decode, f)
        report = DailyReport(None, map(SaleTransaction, raw))
        report.process()
        for x, y in sorted(list(report.by_prod_count.items()), key=itemgetter(1)):
            print(x, y)

