from collections import defaultdict
from decimal import Decimal
from itertools import imap
from operator import itemgetter
import os
from henry.base.serialization import json_loads
from henry.dao.order import Invoice
from .exporting import dump_content


def get_type(prod_id):
    return prod_id


class DailyReport(object):

    def __init__(self, date, raw_inv):
        self._raw_inv = raw_inv
        self.date = date
        self.by_client = defaultdict(Decimal)
        self.by_client_count = defaultdict(int)
        self.by_type = defaultdict(Decimal)
        self.by_type_count = defaultdict(int)
        self.by_prod = defaultdict(Decimal)
        self.by_prod_count = defaultdict(int)
        self.total_value = 0
        self.total_tax = 0
        self.total_count = 0

    def process(self):
        self.by_client = defaultdict(int)
        self.by_client_count = defaultdict(int)
        self.by_type = defaultdict(int)
        self.by_type_count = defaultdict(int)
        self.by_prod = defaultdict(int)
        self.by_prod_count = defaultdict(int)
        self.total_value = 0
        self.total_tax = 0
        self.total_count = 0
        for inv in self._raw_inv:
            self.by_client[inv.meta.client.codigo] += inv.meta.total
            self.by_client_count[inv.meta.client.codigo] += 1
            for i in inv.items:
                val = i.cant * i.prod.precio1 / 100
                self.by_type[get_type(i.prod.prod_id)] += val
                self.by_type_count[get_type(i.prod.prod_id)] += 1
                self.by_prod[i.prod.prod_id] += val
                self.by_prod_count[i.prod.prod_id] += 1
            self.total_value += inv.meta.total
            self.total_tax += inv.meta.tax or 0 
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
        raw = imap(d_, content)
        return raw

    def get(self, day):
        fname = '{}-{}.txt'.format(self.prefix, day.isoformat())
        fname = os.path.join(self.store_dir, fname)
        if not os.path.exists(fname):
            return None
        with open(fname) as f:
            content = self.decode_iter(f.xreadlines())
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
        raw = imap(decode, f.xreadlines())
        report = DailyReport(None, raw, None)
        report.process()
        for x, y in sorted(report.by_client.items(), key=itemgetter(1)):
            print x,y
        for x, y in sorted(report.by_prod_count.items(), key=itemgetter(1)):
            print x,y

