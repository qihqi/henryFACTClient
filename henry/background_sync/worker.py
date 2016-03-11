import requests
import zmq

from henry.base.serialization import SerializableMixin
from henry.externalapi import ExternalApi

__author__ = 'han'

context = zmq.Context()
receiver = context.socket(zmq.SUB)
receiver.connect('tcp://localhost:{}'.format(ZEROMQ_PORT))
receiver.setsockopt(zmq.SUBSCRIBE, '')
externalapi = ExternalApi('http://45.55.88.99:99/api/', 'nota', 'yu', 'yu')



class WorkObject(SerializableMixin):
    _name = ('uid', 'action', 'action_url', 'content', 'desc')

    def __init__(self, uid, action, action_url, content, desc):
        self.uid = uid
        self.action = action
        self.action_url = action_url
        self.content = content
        self.desc = desc


def make_worker_thread(auth):
    def do_work():
        while True:
            work = receiver.recv_pyobj()
            r = requests.request(work.action, work.action_url,
                                 auth=auth, data=work.content)
            if r.status_code == 200:
                # mark complete
                pass
    return do_work
