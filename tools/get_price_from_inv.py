path = '/home/han/Documents/VAR/data/invoice/'

import datetime
import sys
from collections import defaultdict
import os
import json
from henry.invoice.dao import Invoice
from henry.product.dao import PriceList

def get_price_from_inv():
    prod_to_price = defaultdict(list)
    for dirpath, dirnames, filepaths in os.walk(path):
        for f in filepaths:
            full = os.path.join(dirpath, f)
            with open(full) as inv:
                content = inv.read()
                try:
                    invoice = Invoice.deserialize(json.loads(content))
                    for item in invoice.items:
                        if invoice.meta.timestamp < datetime.datetime(2016, 8, 1):
                            print >>sys.stderr, 'too old'
                        prod_to_price[item.prod.prod_id.strip().upper()].append((invoice.meta.timestamp,
                                                            item.prod))
                except:
                    print >>sys.stderr, content
    return prod_to_price

old_path = '/home/han/pricelist2.json'


def get_old_price(path):
    result = {}
    with open(path) as f:
        for x in f.readlines():
            try:
                content = json.loads(x)
                pricelist = PriceList.deserialize(content)
                result[pricelist.prod_id.strip().upper()] = pricelist
            except Exception as ex:
                print >>sys.stderr, ex
                print >>sys.stderr, 'loadingold', x
    return result


def same_price(lhs, rhs):
    return lhs.precio1 == rhs.precio1 and lhs.precio2 == rhs.precio2


def get_last_price(items):
    last_elm = sorted(items, key=lambda x: x[0])[-1][1]
    return last_elm


def get_new_price(prod_to_price):
    result = {}
    for x in prod_to_price:
        result[x] = get_last_price(prod_to_price[x])
    return result

new_path = 'plist.json'
price_new = get_old_price(new_path)
price_old = get_old_price(old_path)
for x in price_new:
    if x not in price_old:
        print ('new', price_new[x].serialize())
    else:
        old_p = price_old[x]
        new_p = price_new[x]
        if not same_price(old_p, new_p):
            print ('alter',  new_p.serialize())

