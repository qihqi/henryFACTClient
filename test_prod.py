from beaker.middleware import SessionMiddleware
from henry.base.dbapi import DBApiGeneric
from henry.product.web import make_wsgi_api

from henry.coreconfig import dbcontext, auth_decorator, sessionmanager
from henry.config import BEAKER_SESSION_OPTS


dbapi = DBApiGeneric(sessionmanager)
application = x = make_wsgi_api(
    'prodapi',
    sessionmanager=sessionmanager,
    auth_decorator=auth_decorator, dbcontext=dbcontext, dbapi=dbapi)
application = SessionMiddleware(application, BEAKER_SESSION_OPTS)

if __name__ == '__main__':
    import bottle
    @x.get('/static/<rest:path>')
    def static(rest):
        return bottle.static_file(rest, root='./static/')
    bottle.run(x)
