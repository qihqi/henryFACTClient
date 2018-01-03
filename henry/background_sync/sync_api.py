import datetime
import uuid
import os
import json
from bottle import Bottle, request
from henry.base.serialization import SerializableMixin, json_dumps
from henry.constants import DATA_ROOT, LOG_UPLOAD_URL
ALM_ID = 0

FINAL_LOG_DIR = os.path.join(DATA_ROOT, 'log_dir/final')
NEW_LOG_DIR = os.path.join(DATA_ROOT, 'log_dir/new')
PROCESSED_LOG_DIR = os.path.join(DATA_ROOT, 'log_dir/processed')


class ActionType:
    NEW_PROD = 'new_prod'
    MODIFY_PROD = 'modify_prod'
    NEW_INV = 'new_inv'
    DELETE_INV = 'delete_inv'
    NEW_TRANS = 'new_inv'
    DELETE_TRANS = 'delete_inv'


class LogMetadata(SerializableMixin):
    _name = (
        'almacen_id',
        'date',
        'batch',
    )


class ChangeLog(SerializableMixin):
    _name = (
        'meta',
        'action_type',
        'content'
    )

def make_date_name(date, batch):
    return '{date}_{batch}'.format(date=date,
                                   batch=batch)


# This is the code that processes the the logs
# for now it just save it.
# this code runs in the remote server.
def make_wsgi_api(prefix):
    app = Bottle()
    
    @app.post(prefix + '/logs')
    def save_logs():
        #json list with all transactions
        raw_content = request.body.read()
        data = json.loads(raw_content)
        meta = LogMetadata.deserialize(data['meta'])
        destination_dir = os.path.join(
                FINAL_LOG_DIR, 
                str(meta.almacen_id))
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
        destination = os.path.join(
            destination_dir, 
            '{date}_{batch}'.format(date=meta.date,
                                    batch=meta.batch))
        with open(destination, 'w') as f:
            f.write(raw_content)
            f.flush()

    return app


# This is the code that uploads the logs to the server
def upload_raw_logs(log_dir, processed_log_dir):
    for name in os.listdir(log_dir):
        fname = os.path.join(processed_log_dir)
        with open(fname) as f:
            data = f.read()
        r = requests.post(LOG_UPLOAD_URL, data=data, auth=auth)
        if r.status_code == 200:
            shutil.move(fname, processed_log_dir) 
        return r.status_code


def _make_log(action, content):
    meta = LogMetadata()
    meta.almacen_id = ALM_ID
    meta.batch = 0
    meta.date = datetime.date.today().isoformat()
    change_log = ChangeLog()
    change_log.meta = meta
    change_log.content = content
    change_log.action_type = action
    return change_log


class SyncApi(object):

    def __init__(self, fileservice):
        self.fileservice = fileservice

    def write_new_prod(self, content):
        change_log = _make_log(ActionType.NEW_PROD, content)
        fname = make_date_name(change_log.meta.date, change_log.meta.batch)
        self.fileservice.append_file(fname, json_dumps(change_log))

    def log_price_list_change(self, clazz, action, pkey, content):
        content = {
            'old': pkey,
            'new': content
        }
        change_log = _make_log(ActionType.MODIFY_PROD, content)
        fname = make_date_name(change_log.meta.date, change_log.meta.batch)
        self.fileservice.append_file(fname, json_dumps(change_log))






if __name__ == '__main__':
    print 'Start Uploading...'
    print 'new dir', NEW_LOG_DIR
    print 'processed dir', PROCESSED_LOG_DIR
    if upload_raw_logs(NEW_LOG_DIR, PROCESSED_LOG_DIR):
        print 'Success'
    else:
        print 'Failed'


