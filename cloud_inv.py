import os
from beaker.middleware import SessionMiddleware

from henry.base.dbapi import DBApiGeneric
from henry.base.fileservice import FileService
from henry.base.session_manager import DBContext
from henry.constants import TRANSACTION_PATH, DATA_ROOT
from henry.coreconfig import sessionmanager, BEAKER_SESSION_OPTS, auth_decorator
from henry.sale_records.dao import InvMovementManager
from henry.product.dao import InventoryApi
from henry.invoice.api import make_nota_all
from henry.config import jinja_env

dbapi = DBApiGeneric(sessionmanager)
dbcontext = DBContext(sessionmanager)
fileservice = FileService(os.path.join(DATA_ROOT, 'inv_logs'))
inventoryapi = InventoryApi(FileService(TRANSACTION_PATH))
invmomanager = InvMovementManager(dbapi, fileservice, inventoryapi)
api = make_nota_all('/sync', dbapi=dbapi,
                    jinja_env=jinja_env,
                    file_manager=fileservice, auth_decorator=auth_decorator)
application = SessionMiddleware(api, BEAKER_SESSION_OPTS)
