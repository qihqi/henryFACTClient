import csv
import json
from operator import itemgetter

import sys

import requests
from coreapi import dbapi
from henry.product.dao import ProdItemGroup, InventoryMovement

params = {
    'start': '2016-05-01',
    'end': '2016-05-31',
}

def main():
    result = {}
    prods = {}
    with dbapi.session:
        for prod in dbapi.search(ProdItemGroup):
            prods[prod.uid] = prod

    for guid in prods:
        data = requests.get('http://192.168.0.23/app/api/itemgroup/{}/transaction'.format(guid), params=params)
        if data.status_code == 200:
            transactions = map(InventoryMovement.deserialize, json.loads(data.text)['results'])
            in_ = 0
            out_ = 0
            for t in transactions:
                if int(t.from_inv_id) == 1:
                    out_ += t.quantity
                if int(t.to_inv_id) == 1:
                    in_ += t.quantity
            result[guid] = (in_, out_)

    writer = csv.writer(sys.stdout, delimiter=',', quotechar='"')
    for x in sorted(result.items(), key=lambda x: x[1][1]):
        p = prods[x[0]]
        writer.writerow([x[0], p.prod_id, p.name, x[1][0], x[1][1]])

def get_profile(guid):
    data = requests.get('http://192.168.0.23/app/api/itemgroup/{}/transaction'.format(guid), params=params)
    result = []
    if data.status_code == 200:
        transactions = map(InventoryMovement.deserialize, json.loads(data.text)['results'])
        current = 0
        for t in transactions:
            if int(t.from_inv_id) == 1:
                current -= t.quantity
            if int(t.to_inv_id) == 1:
                current += t.quantity
            result.append(current)
    print 'here'
    import matplotlib.pyplot as plt
    plt.plot(range(len(result)), result)
    plt.show()
    return result


if __name__ == '__main__':
    #main()
    get_profile(400)
