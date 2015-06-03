import os
import datetime
from bottle import request
from henry.helpers.serialization import SerializableMixin, json_dump
from henry.helpers.fileservice import LockClass


class ActionLog(SerializableMixin):
    _name = (
        'ip_address',
        'username',
        'timestamp',
        'method',
        'url',
        'body',
    )

    def __init__(
            self,
            ip_address=None,
            username=None,
            timestamp=None,
            method=None,
            url=None,
            body=None):
        self.ip_address = ip_address
        self.username = username
        self.timestamp = timestamp
        self.method = method
        self.url = url
        self.body = body


class ActionLogApi:

    def __init__(self, root):
        self.root = root

    def save(self, log):
        if not os.path.exists(self.root):
            os.makedirs(self.root)
        filename = os.path.join(
            self.root, log.timestamp.date().isoformat() + '.actionlog')
        with open(filename, 'a') as f:
            with LockClass(f):
                f.write(json_dump(log.serialize()))
                f.write('\n')
                f.flush()


class ActionLogApiDecor:

    def __init__(self, api):
        self.api = api

    def __call__(self, func):
        def wrapped(*args, **argv):
            log = ActionLog(
                timestamp=datetime.datetime.now(),
                ip_address=request.remote_addr,
                method=request.method,
                url=request.url,
                body=request.body.read())
            self.api.save(log)
            request.body.seek(0)  # reset body to the beginning
            return func(*args, **argv)
        return wrapped
