import shutil

from coreapi import dbapi
from henry.base.serialization import json_dumps
from henry.coreconfig import invapi
from henry.dao.document import Status
from henry.invoice.coreschema import NNota

def fix_inv(uid, old_path):

    inv = invapi.get_doc_from_file(old_path)
    alm_id = 1 if inv.meta.almacen_id == 3 else inv.meta.almacen_id
    for i in inv.items:
        if i.prod.almacen_id is None:
            new_prod = dbapi.getone(prod_id=i.prod.prod_id, almacen_id=alm_id)
            i.prod.almacen_id = new_prod.almacen_id
            i.prod.upi = new_prod.upi
            i.prod.multiplicador = new_prod.multiplicador
    invapi.filemanager.put_file(old_path, json_dumps(inv))
    print 'invoice ', uid, 'saved ', old_path


def main():

    # invs = dbapi.db_session.query(NNota).filter_by(status=Status.NEW).filter(NNota.almacen_id.isnot(None))
    invs = dbapi.db_session.query(NNota).filter_by(uid=10857)

    for i in invs:
        print i.id, i.items_location
        real_path = invapi.filemanager.make_full_path(i.items_location)
        shutil.copy2(real_path, '/tmp')
        fix_inv(i.id, i.items_location)

if __name__ == '__main__':
    #main()
