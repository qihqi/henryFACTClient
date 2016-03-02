from beaker.middleware import SessionMiddleware

from henry.base.dbapi import DBApiGeneric
from henry.invoice.web import make_nota_api
from henry.product.web import make_search_pricelist_api
from henry.users.web import make_client_coreapi
from henry.coreconfig import (BEAKER_SESSION_OPTS, invapi, auth_decorator, pedidoapi,
                              sessionmanager, actionlogged)

dbapi = DBApiGeneric(sessionmanager)
# GET pricelist
queryprod = make_search_pricelist_api('/api', auth_decorator, dbapi)
# POST/PUT invoice
invoice = make_nota_api('/api', dbapi, actionlogged, invapi, auth_decorator, pedidoapi)
# GET CLIENT + AUTH
clientapis = make_client_coreapi('/api', dbapi, actionlogged)
clientapis.merge(queryprod)
clientapis.merge(invoice)
api = clientapis
application = SessionMiddleware(api, BEAKER_SESSION_OPTS)
