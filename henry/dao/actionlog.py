from builtins import object
import os
import datetime

from bottle import request

from henry.base.serialization import SerializableMixin, json_dumps, decode_str
from henry.base.fileservice import LockClass


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


class ActionLogApi(object):

    def __init__(self, root):
        self.root = root

    def save(self, log):
        if not os.path.exists(self.root):
            os.makedirs(self.root)
        filename = os.path.join(
            self.root, log.timestamp.date().isoformat() + '.actionlog')
        with open(filename, 'a') as f:
            with LockClass(f):
                f.write(json_dumps(log.serialize()))
                f.write('\n')
                f.flush()


class ActionLogApiDecor(object):

    def __init__(self, api, workerqueue):
        self.api = api

    def __call__(self, func):
        def wrapped(*args, **argv):
            content = decode_str(request.body.read())
            log = ActionLog(
                timestamp=datetime.datetime.now(),
                ip_address=request.remote_addr,
                method=request.method,
                url=request.url,
                body=content)
            self.api.save(log)
            request.body.seek(0)  # reset body to the beginning
            return func(*args, **argv)
        return wrapped


# Logs changes done to product
class ChangeType(object):
    PRICE_CHANGED = 'price_change'
    CHECK_DATE_CHANGE = 'check_date'
    DELETE_INVOICE = 'delete_invoice'
    CHANGE_INV_TYPE = 'change_inv_type'
    DELETE_PAYMENT = 'delete_payment'
    NEW_PAYMENT = 'new_payment'


class ChangesLog(SerializableMixin):

    _name = (
        'type', 'timestamp', 'incoming_id', 'user_id', 'before', 'after')

    def __init__(self, type_, timestamp, incoming_ip, user_id, before, after):
        self.type = type_
        self.timestamp = timestamp
        self.incoming_ip = incoming_ip
        self.user_id = user_id
        self.before = before
        self.after = after
