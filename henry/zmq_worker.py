import zmq
import json
import time
from multiprocessing import Process
from henry.externalapi import ExternalApi
from henry.config import sessionmanager


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
    receiver.connect("tcp://localhost:1234")
    receiver.setsockopt(zmq.SUBSCRIBE, '')
    api = ExternalApi('http://45.55.88.99/api/', 'nota', 'yu', 'yu')
    print 'worker ready'
    while True:
        s = receiver.recv()
        uid, filepath = json.loads(s)
        print 'received ', uid, filepath
        print 'sleeping 2 secs'
        time.sleep(2)
        with open(filepath) as f:
            api.save_data(f.read())
        with sessionmanager as session:
            session.query(NPedidoTemporal).filter_by(
                    id=uid).update(status='uploaded')
            session.flush()

def start_worker(number=1):
    p = Process(target=do_work)
    p.start()
    print 'worker started'
    return p

if __name__ == '__main__':
    do_work()




