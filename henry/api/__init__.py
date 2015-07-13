from .api_endpoints import api
import bottle


def get_slave():
    from .slave_api import api as slave_api
    from .slave_api import start_server, start_worker
    a = bottle.Bottle()
    a.merge(api)
    a.merge(slave_api)
    start_server()
    start_worker()
    return a


def get_master():
    from .master_api import napi
    a = bottle.Bottle()
    a.merge(api)
    a.merge(napi)
    return a
