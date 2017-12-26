from bottle import Bottle, request
from henry.product.web import create_full_item_from_dict


class ActionType:
    NEW_PROD = 'new_prod'
    MODIFY_PROD = 'modify_prod'
    NEW_INV = 'new_inv'
    DELETE_INV = 'delete_inv'
    NEW_TRANS = 'new_inv'
    DELETE_TRANS = 'delete_inv'


def make_wsgi_api(prefix, dbapi, dbcontext):
    app = Bottle()
    
    @app.post(prefix + '/logs')
    @dbcontext
    def save_logs():
        #json list with all transactions
        content = json.loads(request.body.read())
        for item in content:
            handle_one_item(item)


def handle_one_item(dbapi, item):
    if content['action'] == ActionType.NEW_PROD:
        create_full_item_from_dict(dbapi, content['data'])
    elif content['action'] == ActionType.MODIFY_PROD:
    elif content['action'] == ActionType.NEW_INV:
    elif content['action'] == ActionType.DELETE_INV:
    elif content['action'] == ActionType.NEW_TRANS:
    elif content['action'] == ActionType.DELETE_TRANS:
        pass


