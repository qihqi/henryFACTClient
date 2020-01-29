import datetime
import requests
from henry import constants
from henry import common
from henry.dao.document import Status, DocumentApi
from henry.invoice.dao import NotaExtra
from henry.base.serialization import json_dumps
from henry.base.dbapi import DBApiGeneric

from typing import List, Union


def get_notas_by_dates(dbapi: DBApiGeneric, start: datetime.datetime,
                       end: datetime.datetime) -> List[NotaExtra]:
    with dbapi.session:
        notas = dbapi.db_session.query(NotaExtra.db_class).filter(
                NotaExtra.db_class.last_change_time <= end).filter(
                NotaExtra.db_class.last_change_time >= start).filter(
                    NotaExtra.db_class.status.in_(
                        [Status.COMITTED, Status.DELETED]))
        notas = list(map(NotaExtra.from_db_instance, notas))
        return notas


def send_inv(dbapi: DBApiGeneric, invapi: DocumentApi,
             nota: NotaExtra, send_bytes_func):
    full_inv = invapi.get_doc(nota.uid)
    if full_inv is None:
        print('nota with id {} is none'.format(nota.uid))
        return
    msg = {'inv': full_inv.serialize()}
    msg['method'] = ('put' if nota.status == Status.COMITTED 
                     else 'delete')
    data = json_dumps(msg)
    data_bytes = data.encode('utf-8')
    new_msg = common.aes_encrypt(data_bytes)
    if send_bytes_func(new_msg):
        new_status = nota.status + '_' 
        with dbapi.session:
            dbapi.update(nota, {'status': new_status})
    else:
        print('inv id: {} unsuccessful'.format(nota.uid))


def send_to_remote(dbapi: DBApiGeneric,
                   invapi: DocumentApi,
                   start: datetime.datetime, end: datetime.datetime,
                   send_bytes_func):
    notas = get_notas_by_dates(dbapi, start, end)
    for n in notas:
        try:
            send_inv(dbapi, invapi, n, send_bytes_func)
        except Exception as e:
            print(e)


def main():
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=1)
    def send_bytes_func(msg_bytes):
        resp = requests.post(constants.REMOTE_ADDR, data=msg_bytes)
        print(resp)
        return resp.status_code == 200

    from henry.coreconfig import invapi, sessionmanager
    dbapi = DBApiGeneric(sessionmanager)
    send_to_remote(dbapi, invapi, start, end, send_bytes_func)


if __name__ == '__main__':
    main()
