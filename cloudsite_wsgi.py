from beaker.middleware import SessionMiddleware

from henry.base.dbapi import DBApiGeneric
from henry.base.fileservice import FileService
from henry.base.session_manager import DBContext
from henry.constants import INV_MOVEMENT_PATH, TRANSACTION_PATH
from henry.coreconfig import sessionmanager, BEAKER_SESSION_OPTS, auth_decorator
from henry.sale_records.dao import InvMovementManager
from henry.importation.web import make_import_apis
from henry.product.dao import InventoryApi
from henry.config import jinja_env
from henry.sale_records.web import make_sale_records_api
from henry.background_sync import sync_api

dbapi = DBApiGeneric(sessionmanager)
dbcontext = DBContext(sessionmanager)
fileservice = FileService(INV_MOVEMENT_PATH)
inventoryapi = InventoryApi(FileService(TRANSACTION_PATH))
invmomanager = InvMovementManager(dbapi, fileservice, inventoryapi)
api = import_api = make_import_apis('/import', auth_decorator, dbapi, jinja_env)
records_api = make_sale_records_api('/import', auth_decorator, dbapi,
                                    invmomanager, inventoryapi)
import_api.merge(records_api)
api.merge(sync_api.make_wsgi_api('/import', FileService(sync_api.FINAL_LOG_DIR)))
application = SessionMiddleware(import_api, BEAKER_SESSION_OPTS)
