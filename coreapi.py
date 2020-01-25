from beaker.middleware import SessionMiddleware
from bottle import Bottle
from henry.base.dbapi import DBApiGeneric
from henry.coreconfig import (BEAKER_SESSION_OPTS, invapi, auth_decorator, pedidoapi,
                              sessionmanager, actionlogged)
from henry.invoice.coreapi import make_nota_api
from henry.product.coreapi import make_search_pricelist_api
from henry.users.coreapi import make_client_coreapi

dbapi = DBApiGeneric(sessionmanager)

# GET pricelist
queryprod = make_search_pricelist_api('/api', actionlogged=actionlogged, dbapi=dbapi)
# POST/PUT invoice
invoice = make_nota_api(
    '/api',
    dbapi=dbapi, actionlogged=actionlogged, invapi=invapi, auth_decorator=auth_decorator,
    pedidoapi=pedidoapi, workerqueue=None)
# GET CLIENT + AUTH
clientapis = make_client_coreapi('/api', dbapi, actionlogged)

all_apps = [clientapis, queryprod, invoice]
api = Bottle()
for a in all_apps:
    api.merge(a)
application = SessionMiddleware(api, BEAKER_SESSION_OPTS)

