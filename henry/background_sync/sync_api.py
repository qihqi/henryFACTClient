import os
import json
from bottle import Bottle, request
from henry.product.web import create_full_item_from_dict
from henry.base.serialization import SerializableMixin
from henry.constants import DATA_ROOT, LOG_UPLOAD_URL

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


if __name__ == '__main__':
    print 'Start Uploading...'
    print 'new dir', NEW_LOG_DIR
    print 'processed dir', PROCESSED_LOG_DIR
    if upload_raw_logs(NEW_LOG_DIR, PROCESSED_LOG_DIR):
        print 'Success'
    else:
        print 'Failed'


