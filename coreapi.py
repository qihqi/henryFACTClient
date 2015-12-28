from henry.api.coreapi import make_coreapi
from beaker.middleware import SessionMiddleware
from henry.coreconfig import (BEAKER_SESSION_OPTS, dbcontext, clientapi,
                              invapi, auth_decorator, pedidoapi,
                              sessionmanager, storeapi, usuarioapi, priceapi, actionlogged)

api = make_coreapi(dbcontext, clientapi, invapi, auth_decorator, pedidoapi, sessionmanager,
                   actionlogged, priceapi, usuarioapi, storeapi)
application = SessionMiddleware(api, BEAKER_SESSION_OPTS)
