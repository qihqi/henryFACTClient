from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from jinja2 import Environment, FileSystemLoader
from henry.helpers.fileservice import FileService
from henry.layer2.invoice import InvApiDB, InvApiOld, PedidoApi
from henry.layer2.productos import ProductApiDB, TransApiDB, TransactionApi
from henry.layer2.client import ClientApiDB
from henry.layer1.session_manager import SessionManager
from henry.layer1.db_context import DBContext
from henry.constants import CONN_STRING, INGRESO_PATH, INVOICE_PATH, ENV, LOGIN_URL
from henry.misc import id_type, fix_id, abs_string
from henry.layer1.auth import AuthDecorator
from bottle import auth_basic


engine = create_engine(CONN_STRING)
sessionfactory = sessionmaker(bind=engine)
sessionmanager = SessionManager(sessionfactory)
# this is a decorator
dbcontext = DBContext(sessionmanager)
transactionapi = TransactionApi('/tmp/transactions')
prodapi = ProductApiDB(sessionmanager, transactionapi)

transapi = TransApiDB(sessionmanager, FileService(INGRESO_PATH), prodapi)
invapi = InvApiDB(sessionmanager, FileService(INVOICE_PATH), prodapi)
pedidoapi = PedidoApi(sessionmanager, FileService('/tmp/pedidos'))
invapi2 = InvApiOld(sessionmanager)
clientapi = ClientApiDB(sessionmanager)


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
