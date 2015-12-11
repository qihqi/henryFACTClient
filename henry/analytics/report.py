from collections import defaultdict
from decimal import Decimal
from itertools import imap
from operator import itemgetter
from henry.base.serialization import json_loads
from henry.dao.order import Invoice


def get_type(prod_id):
    return prod_id


class DailyReport(object):

    def __init__(self, date, raw_inv, raw_trans):
        self._raw_inv = raw_inv
        self._raw_trans = raw_trans
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
        for x in self._raw_inv:
            self.by_client[x.meta.client.codigo] += x.meta.total
            self.by_client_count[x.meta.client.codigo] += 1
            for i in x.items:
                val = i.cant * i.prod.precio1 / 100
                self.by_type[get_type(i.prod.prod_id)] += val
                self.by_type_count[get_type(i.prod.prod_id)] += 1
                self.by_prod[i.prod.prod_id]  += val
                self.by_prod_count[i.prod.prod_id] += 1
            self.total_value += x.meta.total
            self.total_tax += x.meta.tax
            self.total_count += 1


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

