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
from henry.hack import fix_id_error


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
    if uid == 'NA' or uid.startswith('9999'):
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
    uid = fix_id_error(uid)
    if uid == 'NA':
        return '9' * 13 # si es consumidor final retorna 13 digitos de 9
    uid = re.sub('[^\d]', '', uid)
    if not validate_uid_and_ruc(uid):
        return '9' * 13
    return uid

jinja_env.globals.update({
    'id_type': id_type,
    'fix_id': fix_id,
})


def validate_uid_and_ruc(uid):
    if len(uid) == 13:
        uid = uid[:10]
    if len(uid) != 10:
        return False
    first_digits = int(uid[:2])
    if first_digits < 1 or first_digits > 24:
        return False

    sum_even = 0
    sum_old = 0
    for i, x in enumerate(uid):
        d = int(x)
        if i % 2 == 1: # it is 0 indexed, so odd positions have even index
            if i == 9:
                continue
            sum_even += d
        else:
            d = (d * 2)
            if d > 9:
                d -= 9
            sum_old += d
    sum_all = sum_even + sum_old
    sum_first_digit = str(sum_all)[0]
    decena = (int(sum_first_digit) + 1) * 10
    validator = decena - sum_all
    if validator == 10:
        validator = 0
    
    return validator == int(uid[-1])
