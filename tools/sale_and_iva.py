from collections import defaultdict
import os
import json
import sys
from henry.invoice.dao import Invoice

__author__ = 'han'


def get_sources(directory):
    for fname in os.listdir(directory):
        if fname.startswith('sale-2015') or fname.startswith('sale-2016'):
            with open(os.path.join(directory, fname)) as f:
                for x in f.xreadlines():
                    yield Invoice.deserialize(json.loads(x))

class SalesData(object):
    def __init__(self):
        self.total = 0
        self.iva = 0
        self.count = 0


def iva_by_month(sources):
    result = defaultdict(SalesData)
    for inv in sources:
        year = inv.meta.timestamp.year
        month = inv.meta.timestamp.month
        ruc = inv.meta.almacen_ruc

        if ruc:
            data = result[(ruc, year, month)]
            data.total += inv.meta.total or 0
            data.iva += inv.meta.tax or 0
            data.count += 1
    return result

def main():
    for x, y in sorted(iva_by_month(get_sources(sys.argv[1])).items()):
        print x, y.total, y.iva, y.count

if __name__ == '__main__':
    main()
