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
from henry.constants import CONN_STRING, INGRESO_PATH, INVOICE_PATH


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


def id_type(uid):
    if uid == 'NA':
        return '07'  # General

    uid = fix_id(uid)
    if len(uid) == 10:
        return '05'  # cedula
    elif len(uid) == 13:
        return '04'  # RUC
    else:
        print 'error!! uid {} with length {}'.format(uid, len(uid))
    return '07'

def fix_id(uid):
    if uid == 'NA':
        return '9' * 13 # si es consumidor final retorna 13 digitos de 9
    uid = re.sub('[^\d]', '', uid)
    return uid

jinja_env.globals.update({
    'id_type': id_type,
    'fix_id': fix_id,
})
