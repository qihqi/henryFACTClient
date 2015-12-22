from beaker.middleware import SessionMiddleware
from henry.base.dbapi import DBApi
from henry.product.dao import ProdItemGroup, Inventory, ProdItem, Product, ProdCount
from henry.product.web import make_wsgi_api

from henry.coreconfig import dbcontext, auth_decorator, storeapi, priceapi, sessionmanager
from henry.config import bodegaapi, itemgroupapi, BEAKER_SESSION_OPTS


itemgroupapi = DBApi(sessionmanager, ProdItemGroup)
itemapi = DBApi(sessionmanager, ProdItem)
inventoryapi = DBApi(sessionmanager, Inventory)
contenidoapi = DBApi(sessionmanager, ProdCount)
prodapi = DBApi(sessionmanager, Product)

application = x = make_wsgi_api(
    sessionmanager=sessionmanager,
    auth_decorator=auth_decorator, dbcontext=dbcontext, storeapi=storeapi, prodapi=prodapi,
    priceapi=priceapi, bodegaapi=bodegaapi, itemapi=itemapi,
    itemgroupapi=itemgroupapi, inventoryapi=inventoryapi,
    contenidoapi=contenidoapi)
application = SessionMiddleware(application, BEAKER_SESSION_OPTS)

if __name__ == '__main__':
    import bottle
    bottle.run(x)
