from beaker.middleware import SessionMiddleware
from henry.accounting.dao import ImageServer, PaymentApi
from henry.base.dbapi import DBApiGeneric
from henry.base.fileservice import FileService
from henry.base.session_manager import DBContext
from henry.config import imagefiles, jinja_env
from henry.constants import INV_MOVEMENT_PATH, TRANSACTION_PATH, USE_ACCOUNTING_APP
from henry.coreconfig import sessionmanager, BEAKER_SESSION_OPTS, auth_decorator, invapi
from henry.importation.dao import InvMovementManager
from henry.importation.web import make_import_apis
from henry.product.dao import InventoryApi
from henry.accounting.web import make_wsgi_api as accapi

dbapi = DBApiGeneric(sessionmanager)
dbcontext = DBContext(sessionmanager)
fileservice = FileService(INV_MOVEMENT_PATH)
inventoryapi = InventoryApi(FileService(TRANSACTION_PATH))
invmomanager = InvMovementManager(dbapi, fileservice, inventoryapi)
api = make_import_apis('/import', auth_decorator, dbapi, invmomanager, inventoryapi)


if USE_ACCOUNTING_APP:
    from PIL import Image as PilImage
    def save_image(imgfile, size, filename):
        im = PilImage.open(imgfile)
        if im.size[0] > size[0]:
            im.resize(size)
        im.save(filename)

    imgserver = ImageServer('/app/img', dbapi, imagefiles, save_image)
    paymentapi = PaymentApi(sessionmanager)

    aapi = accapi(dbapi=dbapi, imgserver=imgserver, dbcontext=dbcontext, paymentapi=paymentapi,
                 auth_decorator=auth_decorator, invapi=invapi)
    api.merge(aapi)

application = SessionMiddleware(api, BEAKER_SESSION_OPTS)
