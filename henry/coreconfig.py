import sys
from bottle import install

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from henry.base.fileservice import FileService
from henry.base.auth import AuthDecorator
from henry.base.session_manager import SessionManager, DBContext
from henry.constants import (CONN_STRING, INVOICE_PATH, ENV,
                             LOGIN_URL, TRANSACTION_PATH, PEDIDO_PATH,
                             ACTION_LOG_PATH,
                             BEAKER_DIR)
from henry.dao.document import DocumentApi, PedidoApi
from henry.invoice.dao import Invoice
from henry.dao.actionlog import ActionLogApi, ActionLogApiDecor
from henry.product.dao import InventoryApi

engine = create_engine(CONN_STRING, pool_recycle=3600, echo=False)
sessionfactory = sessionmaker(bind=engine)
sessionmanager = SessionManager(sessionfactory)
# this is a decorator
dbcontext = DBContext(sessionmanager)

# transactionapi = TransactionApi(sessionmanager, FileService(TRANSACTION_PATH))
transactionapi = InventoryApi(FileService(TRANSACTION_PATH))

invapi = DocumentApi(sessionmanager, FileService(INVOICE_PATH),
                     transactionapi, object_cls=Invoice)

workerqueue = None
# 2020-2-3 disable actionlog. not very useful
# actionlogapi = ActionLogApi(ACTION_LOG_PATH)
# actionlogged = ActionLogApiDecor(actionlogapi, workerqueue)
actionlogged = lambda x: x
pedidoapi = PedidoApi(sessionmanager, filemanager=FileService(PEDIDO_PATH))

# for testing, make auth_decorator do nothing
auth_decorator = lambda x: (lambda y: y)
if ENV == 'prod':
    auth_decorator = AuthDecorator(LOGIN_URL, sessionmanager)

BEAKER_SESSION_OPTS = {
    'session.type': 'file',
    'session.cookie_expires': False,
    'session.data_dir': BEAKER_DIR,
    'session.auto': True
}
