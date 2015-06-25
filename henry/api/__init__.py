from .api_endpoints import api
from .master_api import napi
from .slave_api import api as slave_api
from .slave_api import start_server, start_worker
import bottle


def get_slave():
    a = bottle.Bottle()
    a.merge(api)
    a.merge(slave_api)
    start_server()
    start_worker()
    return a


def get_master():
    a = bottle.Bottle()
    a.merge(api)
    a.merge(napi)
    return a
