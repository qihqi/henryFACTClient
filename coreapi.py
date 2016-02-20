import threading

from Queue import Queue
from beaker.middleware import SessionMiddleware
from bottle import Bottle
from henry.background_sync.worker import make_worker_thread_queued, ForwardRequestProcessor
from henry.base.dbapi import DBApiGeneric
from henry.constants import FORWARD_INV, ZEROMQ_PORT, REMOTE_URL, REMOTE_USER, REMOTE_PASS, CODENAME
from henry.invoice.coreapi import make_nota_api
from henry.product.coreapi import make_search_pricelist_api
from henry.users.coreapi import make_client_coreapi
from henry.coreconfig import (BEAKER_SESSION_OPTS, invapi, auth_decorator, pedidoapi,
                              sessionmanager, actionlogged)

dbapi = DBApiGeneric(sessionmanager)
workerqueue = None
if FORWARD_INV:
    from uwsgidecorators import spoolraw, spool
    processor = ForwardRequestProcessor(dbapi, REMOTE_URL, (REMOTE_USER, REMOTE_PASS), CODENAME)
    @spool
    def method(x):
        processor.forward_request(x)
    workerqueue = method.spool
    print 'started worker thread'


# GET pricelist
actionlogged = lambda x: x

queryprod = make_search_pricelist_api('/api', actionlogged=actionlogged, dbapi=dbapi)
# POST/PUT invoice
invoice = make_nota_api(
    '/api',
    dbapi=dbapi, actionlogged=actionlogged, invapi=invapi, auth_decorator=auth_decorator,
    pedidoapi=pedidoapi, workerqueue=workerqueue)
# GET CLIENT + AUTH
clientapis = make_client_coreapi('/api', dbapi, actionlogged)

all_apps = [clientapis, queryprod, invoice]
api = Bottle()
for a in all_apps:
    api.merge(a)
application = SessionMiddleware(api, BEAKER_SESSION_OPTS)

