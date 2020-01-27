## NOTE: this shit probably doesnt work
import datetime

import requests
from coreapi import dbapi
from henry.background_sync.worker import ForwardRequestProcessor, WorkObject, doc_to_workobject
from henry.coreconfig import invapi
from henry.dao.document import Status
from henry.invoice.dao import Invoice


def main():
    root = 'http://45.55.88.99:99/'
    auth = ('test', 'han')
    processor = ForwardRequestProcessor(dbapi, root, auth, codename='test')

    start = datetime.datetime(2015, 12, 1)
    end = datetime.datetime(2016, 1, 1)
    with dbapi.session:
        for meta in invapi.search_metadata_by_date_range(start, end, status=Status.COMITTED):
            r = requests.get('http://192.168.0.23/api/nota/{}'.format(meta.uid), auth=('yu', 'yu'))
            if r.status_code != 200:
                print r.status_code
                continue
            inv = Invoice.deserialize(r.json())
            work = doc_to_workobject(inv, action=WorkObject.CREATE, objtype=WorkObject.INV)
            processor.exec_work(work)
            print inv.meta.uid,  'created'
            work2 = doc_to_workobject(inv, action=WorkObject.CREATE, objtype=WorkObject.INV_TRANS)
            processor.exec_work(work2)
            print inv.meta.uid,  'commited'

if __name__ == '__main__':
    main()
