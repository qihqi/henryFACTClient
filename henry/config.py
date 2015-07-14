import datetime

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from jinja2 import Environment, FileSystemLoader

from henry.dao import (DocumentApi, Transferencia, Invoice,
                       ProductApiDB, PedidoApi, ClientApiDB,
                       TransactionApi, InvApiOld, PaymentFormat)
from henry.dao.actionlog import ActionLogApi, ActionLogApiDecor
from henry.base.fileservice import FileService
from henry.base.auth import AuthDecorator
from henry.base.session_manager import SessionManager, DBContext
from henry.constants import (CONN_STRING, INGRESO_PATH, INVOICE_PATH, ENV,
                             LOGIN_URL, TRANSACTION_PATH, PEDIDO_PATH, ACTION_LOG_PATH,
                             BEAKER_DIR, EXTERNAL_URL, EXTERNAL_USER, EXTERNAL_PASS, INVOICE_MODE)
from henry.misc import id_type, fix_id, abs_string, value_from_cents, get_total
from henry.externalapi import ExternalApi
import sys
reload(sys)
sys.setdefaultencoding('latin1')

engine = create_engine(CONN_STRING, pool_recycle=3600)
sessionfactory = sessionmaker(bind=engine)
sessionmanager = SessionManager(sessionfactory)
# this is a decorator
dbcontext = DBContext(sessionmanager)

transactionapi = TransactionApi(sessionmanager, FileService(TRANSACTION_PATH))
prodapi = ProductApiDB(sessionmanager)
pedidoapi = PedidoApi(sessionmanager, FileService(PEDIDO_PATH))
clientapi = ClientApiDB(sessionmanager)

transapi = DocumentApi(sessionmanager, FileService(INGRESO_PATH), transactionapi, object_cls=Transferencia)
invapi = DocumentApi(sessionmanager, FileService(INVOICE_PATH), transactionapi, object_cls=Invoice)

invapi2 = InvApiOld(sessionmanager)
externaltransapi = ExternalApi(EXTERNAL_URL, 'ingreso', EXTERNAL_USER, EXTERNAL_PASS)
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
    'today': datetime.date.today,
    'PaymentFormat': PaymentFormat,
})

BEAKER_SESSION_OPTS = {
    'session.type': 'file',
    'session.cookie_expires': False,
    'session.data_dir': BEAKER_DIR,
    'session.auto': True
}

BODEGAS_EXTERNAS = (
    ('POLICENTRO', externaltransapi, 1),  # nombre, api, numero de bodega
)

