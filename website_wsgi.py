from beaker.middleware import SessionMiddleware
from bottle import Bottle

from henry.accounting.dao import ImageServer, PaymentApi
from henry.advanced import make_experimental_apps
from henry.users.web import make_wsgi_app as userwsgi
from henry.accounting.web import make_wsgi_app as accwsgi
from henry.accounting.web import make_wsgi_api as accapi
from henry.product.web import make_wsgi_app as prodapp
from henry.product.web import make_wsgi_api as prod_api_app
from henry.inventory.web import make_inv_wsgi, make_inv_api
from henry.invoice.websites import make_invoice_wsgi
from henry.importation.web import make_import_apis
from henry.base.dbapi import DBApiGeneric
from henry.constants import USE_ACCOUNTING_APP, FORWARD_INV, ZEROMQ_PORT
from henry.config import (BEAKER_SESSION_OPTS, jinja_env, transapi,
                          imagefiles, paymentapi, BODEGAS_EXTERNAS)
from henry.coreconfig import (dbcontext, auth_decorator, sessionmanager,
                              actionlogged, invapi, pedidoapi)
from henry.web import webmain
from henry.api.api_endpoints import api

dbapi = DBApiGeneric(sessionmanager)

userapp = userwsgi(dbcontext, auth_decorator, jinja_env, dbapi, actionlogged)
invoiceapp = make_invoice_wsgi(dbapi, auth_decorator, actionlogged, invapi, pedidoapi, jinja_env)
invapp = make_inv_wsgi(dbapi, jinja_env, actionlogged, auth_decorator, transapi,
                       revisionapi=None, external_bodegas=BODEGAS_EXTERNAS)
invappapi = make_inv_api(dbapi, transapi, auth_decorator, actionlogged)
papp = prodapp(dbcontext, auth_decorator, jinja_env, dbapi, imagefiles)
advanced = make_experimental_apps(dbapi, invapi, auth_decorator, jinja_env, transactionapi)
import_api = make_import_apis('/app/api', dbapi)

create_prod_api = prod_api_app(
    '/app/api',
    sessionmanager=sessionmanager,
    auth_decorator=auth_decorator, dbcontext=dbcontext,
    dbapi=dbapi, inventoryapi=transactionapi)
all_apps = [webmain, api, userapp, invoiceapp, invapp, papp, create_prod_api]

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
    app.merge(api)
    app.merge(accapp)

if FORWARD_INV:
    from henry.background_sync.workerqueue import make_worker_push_queue
    queue = make_worker_push_queue(ZEROMQ_PORT)
    for a in all_apps:
        a.install(queue)
app = Bottle()
for a in all_apps:
    app.merge(a)
application = SessionMiddleware(app, BEAKER_SESSION_OPTS)
