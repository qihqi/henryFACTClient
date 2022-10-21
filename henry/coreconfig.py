from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from henry.base.fileservice import FileService
from henry.base.auth import AuthDecorator
from henry.base.session_manager import SessionManager, DBContext
from henry import constants
from henry.constants import (CONN_STRING, INVOICE_PATH, ENV,
                             LOGIN_URL, TRANSACTION_PATH, PEDIDO_PATH,
                             BEAKER_DIR)
from henry.dao.document import DocumentApi, PedidoApi
from henry.invoice.dao import Invoice
from henry.product.dao import InventoryApi
from henry.invoice.util import WsEnvironment

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
def actionlogged(x):
    return x


pedidoapi = PedidoApi(sessionmanager, filemanager=FileService(PEDIDO_PATH))


# for testing, make auth_decorator do nothing
def auth_decorator(x):
    return (lambda y: y)


if ENV == 'prod':
    auth_decorator = AuthDecorator(LOGIN_URL, sessionmanager)

BEAKER_SESSION_OPTS = {
    'session.type': 'file',
    'session.cookie_expires': False,
    'session.data_dir': BEAKER_DIR,
    'session.auto': True
}

WS_PROD = WsEnvironment(
    'PRODUCCION', '2',
    'https://cel.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl',
    'https://cel.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
)

WS_TEST = WsEnvironment(
    'PRUEBA',
    '1',
    'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/RecepcionComprobantesOffline?wsdl',
    'https://celcer.sri.gob.ec/comprobantes-electronicos-ws/AutorizacionComprobantesOffline?wsdl'
)

quinal_ws = WS_PROD if constants.QUINAL_WS_PROD else WS_TEST
corp_ws = WS_PROD if constants.CORP_WS_PROD else WS_TEST
