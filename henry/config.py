import datetime

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from jinja2 import Environment, FileSystemLoader

from henry.dao import (DocumentApi, Transferencia, Invoice,
                       ProductApiDB, PedidoApi, ClientApiDB,
                       TransactionApi, InvApiOld)
from henry.dao.actionlog import ActionLogApi, ActionLogApiDecor
from henry.base.fileservice import FileService
from henry.base.auth import AuthDecorator
from henry.base.session_manager import SessionManager, DBContext
from henry.constants import (CONN_STRING, INGRESO_PATH, INVOICE_PATH, ENV,
                             LOGIN_URL, TRANSACTION_PATH, PEDIDO_PATH, ACTION_LOG_PATH,
                             BEAKER_DIR)
from henry.misc import id_type, fix_id, abs_string, value_from_cents, get_total
from henry.externalapi import ExternalApi
import sys
reload(sys)
sys.setdefaultencoding('latin1')

engine = create_engine(CONN_STRING)
sessionfactory = sessionmaker(bind=engine)
sessionmanager = SessionManager(sessionfactory)
# this is a decorator
dbcontext = DBContext(sessionmanager)

transactionapi = TransactionApi(TRANSACTION_PATH)
prodapi = ProductApiDB(sessionmanager, transactionapi)
pedidoapi = PedidoApi(sessionmanager, FileService(PEDIDO_PATH))
clientapi = ClientApiDB(sessionmanager)

transapi = DocumentApi(sessionmanager, FileService(INGRESO_PATH), prodapi, object_cls=Transferencia)
invapi = DocumentApi(sessionmanager, FileService(INVOICE_PATH), prodapi, object_cls=Invoice)
invapi2 = InvApiOld(sessionmanager)
externaltransapi = ExternalApi('http://186.68.43.214/api/', 'ingreso', 'yu', 'yu')
actionlogapi = ActionLogApi(ACTION_LOG_PATH)
actionlogged = ActionLogApiDecor(actionlogapi)

def my_finalize(x):
    return '' if x is None else x
template_paths = ['./templates']
jinja_env = Environment(loader=FileSystemLoader(template_paths), finalize=my_finalize)

# for testing, make auth_decorator do nothing
auth_decorator = lambda x: x
if ENV == 'prod':
    auth_decorator = AuthDecorator(LOGIN_URL, sessionmanager)

jinja_env.globals.update({
    'id_type': id_type,
    'fix_id': fix_id,
    'abs': abs_string,
    'value_from_cents': value_from_cents,
    'get_total': get_total,
    'today': datetime.date.today
})

BEAKER_SESSION_OPTS = {
    'session.type': 'file',
    'session.cookie_expires': False,
    'session.data_dir': BEAKER_DIR,
    'session.auto': True
}
