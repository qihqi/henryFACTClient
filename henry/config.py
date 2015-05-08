import re
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from jinja2 import Environment, FileSystemLoader
from henry.helpers.fileservice import FileService
from henry.layer2.productos import ProductApiDB, TransApiDB
from henry.layer2.invoice import InvApiDB, InvApiOld
from henry.layer2.client import ClientApiDB
from henry.layer1.session_manager import SessionManager
from henry.layer1.db_context import DBContext
from henry.constants import CONN_STRING, INGRESO_PATH, INVOICE_PATH, ENV
from henry.hack import fix_id_error
from henry.misc import id_type, fix_id, validate_uid_and_ruc, abs_string
from henry.constants import LOGIN_URL
from henry.layer1.auth import AuthDecorator


engine = create_engine(CONN_STRING)
sessionfactory = sessionmaker(bind=engine)
sessionmanager = SessionManager(sessionfactory)
# this is a decorator
dbcontext = DBContext(sessionmanager)
prodapi = ProductApiDB(sessionmanager)

transapi = TransApiDB(sessionmanager, FileService(INGRESO_PATH), prodapi)
invapi = InvApiDB(sessionmanager, FileService(INVOICE_PATH), prodapi)
invapi2 = InvApiOld(sessionmanager)
clientapi = ClientApiDB(sessionmanager)


template_paths = ['./templates']
jinja_env = Environment(loader=FileSystemLoader(template_paths))

# for testing, make auth_decorator do nothing
auth_decorator = lambda x: x
if ENV == 'prod':
    auth_decorator = AuthDecorator(dbcontext, LOGIN_URL)

jinja_env.globals.update({
    'id_type': id_type,
    'fix_id': fix_id,
    'abs' : abs_string,
})
