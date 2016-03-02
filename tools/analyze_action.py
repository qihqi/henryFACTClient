from henry.dao.actionlog import ActionLog
from henry.config import sessionmanager

import os
import sys
import json
import requests
from datetime import date, timedelta
from henry.invoice.dao import Invoice
from henry.product.schema import NProdTag


def process(content, ip_to_prod):
    for line in content: 
        if not line:
            continue
        act = ActionLog.deserialize(json.loads(line))
        if act.method == 'POST' and act.url.endswith('pedido'):
            inv = Invoice.deserialize(json.loads(act.body))
            for x in inv.items:
                ip_to_prod[act.ip_address].add(x.prod.codigo.upper())


def process_dict(ip_to_prod):
    g1 = ip_to_prod['192.168.0.51'] | ip_to_prod['192.168.0.52'] | ip_to_prod['192.168.0.53']
    g2 = ip_to_prod['192.168.0.54']
    g3 = ip_to_prod['192.168.0.55']
    g4 = ip_to_prod['192.168.0.56']

    print 'group 1', g1  # plasticos
    print 'group 2', g2  # finos
    print 'group 3', g3  # aplique tira vinchas
    print 'group 4', g4  # flores

    with sessionmanager as session:
        insert_all(session, g1, 'bisuteria')
        insert_all(session, g2, 'bisuteria_fino')
        insert_all(session, g3, 'material_ropa')
        insert_all(session, g4, 'flores')
        session.commit()


def insert_all(session, content, tagtext):
    for x in content:
        exists = session.query(NProdTag).filter_by(prod_id=x, tag=tagtext).first()
        if not exists:
            tag = NProdTag(tag=tagtext, prod_id=x)
            session.add(tag)

def main():
    start = date(2015, 7, 1)
    end = date(2015, 8, 31)
    while start < end:
        url = 'http://192.168.0.22/data/actionlog/{}.actionlog'.format(start.isoformat())
        resp = requests.get(url)
        if resp.status_code == 200:
            print 'processing ', start.isoformat()
            with open(os.path.join(sys.argv[1], start.isoformat()), 'w') as f:
                f.write(resp.content)
        start = start + timedelta(days=1)


main()
