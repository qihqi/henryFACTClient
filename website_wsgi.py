from beaker.middleware import SessionMiddleware

from henry.accounting.dao import ImageServer, PaymentApi
from henry.users.web import make_wsgi_app as userwsgi
from henry.accounting.web import make_wsgi_app as accwsgi
from henry.accounting.web import make_wsgi_api as accapi
from henry.product.web import make_wsgi_app as prodapp
from henry.product.web import make_wsgi_api as prod_api_app
from henry.inventory.web import make_inv_wsgi
from henry.invoice.websites import make_invoice_wsgi
from henry.base.dbapi import DBApiGeneric
from henry.constants import USE_ACCOUNTING_APP
from henry.config import (BEAKER_SESSION_OPTS, jinja_env, prodapi, transapi,
                          revisionapi, bodegaapi, imagefiles, paymentapi)
from henry.coreconfig import (dbcontext, auth_decorator, sessionmanager,
                              actionlogged, invapi, pedidoapi)
from henry.api.api_endpoints import api
from henry.web import webmain as app
from henry.advanced import webadv

dbapi = DBApiGeneric(sessionmanager)

userapp = userwsgi(dbcontext, auth_decorator, jinja_env, dbapi, actionlogged)
invoiceapp = make_invoice_wsgi(dbapi, auth_decorator, actionlogged, invapi, pedidoapi, jinja_env)
invapp = make_inv_wsgi(jinja_env, dbcontext, actionlogged, auth_decorator,
                       sessionmanager, prodapi, transapi, revisionapi, bodegaapi)
papp = prodapp(dbcontext, auth_decorator, jinja_env, dbapi, imagefiles)

create_prod_api = prod_api_app(
    '/app/api',
    sessionmanager=sessionmanager,
    auth_decorator=auth_decorator, dbcontext=dbcontext, dbapi=dbapi)

app.merge(api)
app.merge(userapp)
app.merge(invoiceapp)
app.merge(invapp)
app.merge(papp)
app.merge(create_prod_api)

if USE_ACCOUNTING_APP:
    from PIL import Image as PilImage

    def save_image(imgfile, size, filename):
        im = PilImage.open(imgfile)
        if im.size[0] > size[0]:
            im.resize(size)
        im.save(filename)

    imgserver = ImageServer('/app/img', dbapi, imagefiles, save_image)
    paymentapi = PaymentApi(sessionmanager)
    accapp = accwsgi(dbcontext, imgserver,
                     dbapi, paymentapi, jinja_env, auth_decorator, imagefiles, invapi)
    api = accapi(dbapi=dbapi, imgserver=imgserver, dbcontext=dbcontext, paymentapi=paymentapi,
                 auth_decorator=auth_decorator, invapi=invapi)
    app.merge(accapp)
    app.merge(api)

application = SessionMiddleware(app, BEAKER_SESSION_OPTS)
