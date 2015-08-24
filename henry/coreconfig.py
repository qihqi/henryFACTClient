from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from henry.base.fileservice import FileService
from henry.base.auth import AuthDecorator
from henry.base.dbapi import DBApi
from henry.base.session_manager import SessionManager, DBContext
from henry.constants import (CONN_STRING, INVOICE_PATH, ENV,
                             LOGIN_URL, TRANSACTION_PATH, PEDIDO_PATH,
                             ACTION_LOG_PATH,
                             BEAKER_DIR)
from henry.dao.coredao import PriceList, Client, User, Store, TransactionApi
from henry.dao.document import DocumentApi, PedidoApi
from henry.dao.order import Invoice

from henry.dao.actionlog import ActionLogApi, ActionLogApiDecor
import sys
reload(sys)
sys.setdefaultencoding('utf8')

engine = create_engine(CONN_STRING, pool_recycle=3600, echo=True)
sessionfactory = sessionmaker(bind=engine)
sessionmanager = SessionManager(sessionfactory)
# this is a decorator
dbcontext = DBContext(sessionmanager)

transactionapi = TransactionApi(sessionmanager, FileService(TRANSACTION_PATH))
pedidoapi = PedidoApi(sessionmanager, FileService(PEDIDO_PATH))
clientapi = DBApi(sessionmanager, Client)
priceapi = DBApi(sessionmanager, PriceList)
usuarioapi = DBApi(sessionmanager, User)
storeapi = DBApi(sessionmanager, Store)

invapi = DocumentApi(sessionmanager, FileService(INVOICE_PATH),
                     transactionapi, object_cls=Invoice)
actionlogapi = ActionLogApi(ACTION_LOG_PATH)
actionlogged = ActionLogApiDecor(actionlogapi)

# for testing, make auth_decorator do nothing
auth_decorator = lambda x: x
if ENV == 'prod':
    auth_decorator = AuthDecorator(LOGIN_URL, sessionmanager)

BEAKER_SESSION_OPTS = {
    'session.type': 'file',
    'session.cookie_expires': False,
    'session.data_dir': BEAKER_DIR,
    'session.auto': True
}
