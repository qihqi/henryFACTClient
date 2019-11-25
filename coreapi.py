from __future__ import print_function
from beaker.middleware import SessionMiddleware
from bottle import Bottle
from henry.background_sync.worker import ForwardRequestProcessor
from henry.base.dbapi import DBApiGeneric
from henry.base.session_manager import SessionManager
from henry.constants import FORWARD_INV, REMOTE_URL, REMOTE_USER, REMOTE_PASS, CODENAME
from henry.coreconfig import (BEAKER_SESSION_OPTS, invapi, auth_decorator, pedidoapi,
                              sessionmanager, actionlogged, engine, sessionfactory)
from henry.invoice.coreapi import make_nota_api
from henry.product.coreapi import make_search_pricelist_api
from henry.users.coreapi import make_client_coreapi
from sqlalchemy.orm import sessionmaker

dbapi = DBApiGeneric(sessionmanager)
workerqueue = None


if FORWARD_INV:
    from uwsgidecorators import spool
    session = SessionManager(sessionfactory)
    # need a different session for processor, as it might run outside
    # of a http request context
    dbapi2 = DBApiGeneric(session)
    processor = ForwardRequestProcessor(dbapi2, REMOTE_URL, (REMOTE_USER, REMOTE_PASS), CODENAME)
    @spool
    def method(x):
        processor.forward_request(x)
    workerqueue = method.spool
    print('started worker thread')

actionlogged = lambda x: x

# GET pricelist
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

