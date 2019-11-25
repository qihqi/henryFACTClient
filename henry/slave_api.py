from __future__ import print_function
from builtins import object
from multiprocessing import Process

import zmq

from bottle import Bottle, json_loads

from henry.base.serialization import json_dumps
from henry.dao.document import Status
from henry.invoice.dao import InvMetadata, Invoice
from henry.invoice.coreschema import NPedidoTemporal
from henry.coreconfig import (pedidoapi, sessionmanager,
                              dbcontext, auth_decorator, actionlogged)
from henry.externalapi import ExternalApi
from henry.invoice.coreapi import InvoiceOptions

api = Bottle()

ZEROMQ_PORT = 1234


class Command(object):
    SAVE = 'save'
    COMMIT = 'commit'

    def __init__(self, command, uid, path=None):
        self.command = command
        self.uid = uid
        self.path = path


def do_work():
    context = zmq.Context()
    receiver = context.socket(zmq.SUB)
    receiver.connect('tcp://localhost:{}'.format(ZEROMQ_PORT))
    receiver.setsockopt(zmq.SUBSCRIBE, '')
    externalapi = ExternalApi('http://45.55.88.99:99/api/', 'nota', 'yu', 'yu')
    print('worker ready')

    while True:
        s = receiver.recv_pyobj()
        if s.command == Command.SAVE:
            with open(s.path) as f:
                data = json_loads(f.read())
                options = InvoiceOptions()
                options.incrementar_codigo = False
                options.revisar_producto = False
                options.crear_cliente = True
                data['options'] = options
                del data.timestamp
                serialized = json_dumps(data.serialize())
                codigo = externalapi.save(serialized).json()['codigo']
                with sessionmanager as session:
                    session.query(NPedidoTemporal).filter_by(
                        id=s.uid).update({
                            NPedidoTemporal.status: 'uploaded',
                            NPedidoTemporal.external_id: codigo})
                    session.flush()
        elif s.command == Command.COMMIT:
            t = Invoice(InvMetadata, [])
            with sessionmanager as session:
                temp = session.query(NPedidoTemporal).filter_by(id=s.uid).first()
                if temp.external_id is not None:
                    t.meta.uid = temp.external_id
                    externalapi.commit(t)


def start_worker():
    p = Process(target=do_work)
    p.start()
    print('worker started')
    return p


workerqueue = None


def start_server():
    context = zmq.Context()
    queue = context.socket(zmq.PUB)
    ADDR = "tcp://*:1234"
    queue.bind(ADDR)
    global workerqueue
    workerqueue = queue
    return queue


def post_inv(json_content):
    uid, path = pedidoapi.save(json_content)
    command = Command(Command.SAVE, uid, path)
    workerqueue.send_pyobj(command)
    return {'codigo': uid}


@api.put('/api/nota/<uid>')
@dbcontext
@auth_decorator(0)
@actionlogged
def put_inv(uid):
    command = Command(Command.COMMIT, uid)
    workerqueue.send_pyobj(command)
    return {'status': Status.COMITTED}
