from collections import defaultdict
import os
import json
import sys
from henry.base.serialization import json_dumps
from henry.dao.document import Status
from henry.invoice.dao import Invoice

__author__ = 'han'


def get_sources(directory):
    for fname in os.listdir(directory):
        if fname.startswith('sale') or fname.startswith('inv'):
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
        if inv.meta.status == Status.DELETED:
            continue
        year = inv.meta.timestamp.year
        month = inv.meta.timestamp.month
        ruc = inv.meta.almacen_ruc

        if inv.meta.almacen_id:
            data = result[(inv.meta.almacen_id == 2, year, month)]
            data.total += inv.meta.total or 0
            data.iva += inv.meta.tax or 0
            data.count += 1
    return result

def main():
    for x, y in sorted(iva_by_month(get_sources(sys.argv[1])).items()):
        print x, y.total, y.iva, y.count

def get_rows():
    x = []
    for i in get_sources(sys.argv[1]):
        x.append(i.meta)
    print json_dumps(x)

if __name__ == '__main__':
   # main()
    get_rows()
