import json
import os
import random
import sys
from decimal import Decimal
import datetime
import subprocess

from henry.invoice.dao import InvMetadata, Invoice
from henry.dao.document import Status, Item
from henry.dao.transaction import Client
from henry.base.serialization import json_dumps
from henry.coreconfig import priceapi, sessionmanager
from henry.product.dao import PriceList

START = datetime.date(2015, 12, 01)
END = datetime.date(2015, 12, 29)
VAL_PER_INV = 280000
INV_PER_DAY = 3
TOTAL_VAL = 20000000
START_CODE = 1


TWO = Decimal('0.01')
SAVE = True
DIR = './print_dir'
PRINT_DIR = os.path.join(DIR, 'to_be_printed')
JSON_DIR = os.path.join(DIR, 'json_files')


def copystring(string, position, dest):
    x, y = position
    for i in string:
        if y < len(dest) and x < len(dest[y]):
            dest[y][x] = i
            x += 1

SIZE = (60, 31)

pos = {
    'fecha': (31, 3),
    'nombre': (4, 4),
    'ruc': (3, 3),
    'dir': (5, 5),
    'cant': (1, 8),
    'desc': (6, 8),
    'price': (34, 8),
    'sub': (40, 8),
    'subtotal': (2, 25),
    'subtotal2': (14, 25),
    'total': (40, 26),
    'iva': (40, 25),
}

def write_header(header, content):
    copystring(header.timestamp.date().isoformat(), pos['fecha'], content)
    copystring(header.client.name, pos['nombre'], content)
    copystring(header.client.codigo, pos['ruc'], content)
    copystring('Boyaca 1515 y Aguirre', pos['dir'], content)

def disp(n):
    return '%d.%02d' % (n/100, n%100)


def write_out_inv(header, items, content):
    write_header(header, content)
    y = pos['cant'][1]
    for i in items:
        price = i.prod.precio1
        cant = int(i.cant)
        subt = int(price * cant)

        copystring(str(cant), (pos['cant'][0], y), content)
        copystring(str(i.prod.nombre), (pos['desc'][0], y), content)
        copystring(disp(price), (pos['price'][0], y), content)
        copystring(disp(subt), (pos['sub'][0], y), content)
        y += 1
    copystring(disp(header.subtotal), pos['subtotal'], content)
    copystring(disp(header.tax), pos['iva'], content)
    copystring(disp(header.total), pos['total'], content)



def print_inv_file(inv, thefile):
    content = []
    for i in range(SIZE[1]):
        y = [' '] * SIZE[0]
        content.append(y)
    write_out_inv(inv.meta, inv.items, content)
    for x in content[1:]:
        print >>thefile, ''.join(x).rstrip()

def group_by(items):
    result = {}
    for i in items:
        if i.prod.prod_id in result:
            result[i.prod.prod_id].cant += i.cant
        else:
            result[i.prod.prod_id] = i
    return result.values()


def getallitems():
    return priceapi.search(almacen_id=2)


def randitems(items, size):
    result = set()
    while len(result) < size:
        result.add(random.choice(items))
    return result

def make_rand_itemlist(target_total, all_items):
    items = randitems(all_items, 10)
    result = []
    for x in items:
        cant = random.randint(8, 12)
        i = Item(prod=x, cant=cant)
        result.append(i)
    total = sum((x.cant * x.prod.precio1 for x in result))
    mult = target_total / total
    for x in result:
        x.cant *= mult
    return result


def get_price_list():
    fname = os.path.join(DIR, 'prodlist.json')
    if os.path.exists(fname):
        with open(fname) as f:
            all_items = json.loads(f.read())
            all_items = map(PriceList.deserialize, all_items)
            print 'loaded from disk'
    else:
        with sessionmanager:
            all_items = list(getallitems())
        with open(fname, 'w') as f:
            f.write(json_dumps(all_items))
            f.flush()
            print 'price list saved to disk'
    return all_items


def make_one_inv(day, codigo, items):
    invmeta = InvMetadata()
    invmeta.codigo = codigo
    invmeta.timestamp = day
    invmeta.status = Status.NEW
    invmeta.bodega_id = 1
    invmeta.almacen_ruc = '0992584092001'
    invmeta.almacen_id = 3
    invmeta.payment_format = 'EFECTIVO'
    invmeta.subtotal = sum((int(i.cant * i.prod.precio1) for i in items))
    invmeta.tax = int(invmeta.subtotal * 0.12)
    invmeta.tax_percent = int(invmeta.subtotal * 0.12)
    invmeta.total = invmeta.subtotal + invmeta.tax
    invmeta.discount = 0

    invmeta.client = Client()
    invmeta.client.name = 'QUINAL SA'
    invmeta.client.codigo = '0992337168001'

    inv = Invoice(invmeta, items)
    return inv

def write_inv_json(inv):
    options = InvoiceOptions()
    options.no_alm_id = True
    options.usar_decimal = True
    inv_data = inv.serialize()
    inv_data['options'] = options
    inv_str = json_dumps(inv_data)
    fname = os.path.join(JSON_DIR, inv.meta.codigo + '.json')
    with open(fname, 'w') as f:
        f.write(inv_str)
    print >>sys.stderr, ('escrito en el disco')


def print_inv(inv):
    fname = os.path.join(PRINT_DIR, inv.meta.codigo + '.json')
    with open(fname, 'w') as f:
        print_inv_file(inv, f)
        print 'printed ', fname

def print_one_by_one():
    all_files = os.listdir(PRINT_DIR)
    all_files = sorted(all_files, key=lambda x: int(x.split('.')[0]))
    for f in all_files:
        if 'printed' not in f:
            fname = os.path.join(PRINT_DIR, f)
            result = raw_input('will print {} ?'.format(fname))
            if result == 'y':
                print 'running lpr '
                subprocess.call(['lpr', fname])
                os.rename(fname, fname+'printed')


def skipday(day):
    return day.isoweekday() == 7 or day == datetime.date(2015, 12, 25)


def get_saved_inv():
    for x in os.listdir(JSON_DIR):
        with open(os.path.join(JSON_DIR, x)) as f:
            yield Invoice.deserialize(json.loads(f.read()))

def print_sum(inv_list):
    total = 0
    iva = 0
    for inv in inv_list:
        if inv.meta.codigo == '49' or inv.meta.codigo == '67':
            for i, r in enumerate(inv.items):
                if r.prod.prod_id == 'E':
                    del i.items[i]
            t1 = sum(int(x.prod.precio1 * x.cant) for x in inv.items)
            total += t1
            iva += int(0.12 * t1)
        total += inv.meta.subtotal
        iva += inv.meta.tax
    return total, iva




def main():
    print print_sum(get_saved_inv())
    return

    if len(sys.argv) > 1 and sys.argv[1] == 'print':
        print_one_by_one()
        return
    all_items = get_price_list()
    current_day = START
    current_num = int(START_CODE)
    total = 0
    while current_day < END:
        print 'day', current_day, '-------------------',
        if not skipday(current_day):
            realtime = datetime.datetime.combine(current_day, datetime.datetime.min.time())
            for i in range(INV_PER_DAY):
                items = make_rand_itemlist(VAL_PER_INV, all_items)
                inv = make_one_inv(realtime, str(current_num), items)
                print_inv(inv)
                write_inv_json(inv)
                total += inv.meta.total
                current_num += 1
        current_day += datetime.timedelta(days=1)
    print >>sys.stderr, 'impreso bien', total



if __name__ == '__main__':
    main()
