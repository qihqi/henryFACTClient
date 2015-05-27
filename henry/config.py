from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from jinja2 import Environment, FileSystemLoader

from henry.dao import (DocumentApi, Transferencia, Invoice,
                       ProductApiDB, PedidoApi, ClientApiDB,
                       TransactionApi, InvApiOld)

from henry.helpers.fileservice import FileService
from henry.layer1.auth import AuthDecorator
from henry.layer1.session_manager import SessionManager
from henry.layer1.db_context import DBContext
from henry.constants import (CONN_STRING, INGRESO_PATH, INVOICE_PATH, ENV,
                             LOGIN_URL, TRANSACTION_PATH, PEDIDO_PATH)

from henry.misc import id_type, fix_id, abs_string

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

template_paths = ['./templates']
jinja_env = Environment(loader=FileSystemLoader(template_paths))

# for testing, make auth_decorator do nothing
auth_decorator = lambda x: x
if ENV == 'prod':
    auth_decorator = AuthDecorator(LOGIN_URL, sessionmanager)

jinja_env.globals.update({
    'id_type': id_type,
    'fix_id': fix_id,
    'abs': abs_string,
})