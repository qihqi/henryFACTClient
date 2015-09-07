import datetime
import os

from jinja2 import Environment, FileSystemLoader

from henry.base.fileservice import FileService
from henry.base.dbapi import DBApi
from henry.constants import (
    INGRESO_PATH, BEAKER_DIR,
    EXTERNAL_URL, EXTERNAL_USER, EXTERNAL_PASS,
    IMAGE_PATH)
from henry.dao.comments import ImageServer, Image

from henry.dao.payment import PaymentApi
from henry.dao.productos import (
    RevisionApi, ProdCount, Product, Bodega, Category, ProdApi, ProdItem, ProdItemGroup)
from henry.dao.document import DocumentApi
from henry.dao.inventory import Transferencia
from henry.dao.order import PaymentFormat

from henry.misc import id_type, fix_id, abs_string, value_from_cents, get_total
from henry.externalapi import ExternalApi
from henry.coreconfig import (sessionmanager, transactionapi, priceapi,
                              storeapi)

sm = sessionmanager
countapi = DBApi(sessionmanager, ProdCount)
revisionapi = RevisionApi(sessionmanager, countapi, transactionapi)
paymentapi = PaymentApi(sessionmanager)
imagefiles = FileService(IMAGE_PATH)
transapi = DocumentApi(sessionmanager, FileService(INGRESO_PATH),
                       transactionapi, object_cls=Transferencia)
bodegaapi = DBApi(sessionmanager, Bodega)
prodapi = ProdApi(sm, storeapi, bodegaapi,
                  DBApi(sm, Product),
                  DBApi(sm, ProdCount),
                  priceapi, DBApi(sm, Category))
itemgroupapi = DBApi(sessionmanager, ProdItemGroup)

externaltransapi = ExternalApi(EXTERNAL_URL, 'ingreso',
                               EXTERNAL_USER, EXTERNAL_PASS)

imgserver = ImageServer('/app/img', DBApi(sm, Image), imagefiles)


def my_finalize(x):
    return '' if x is None else x


template_paths = ['./templates']
jinja_env = Environment(loader=FileSystemLoader(template_paths),
                        finalize=my_finalize)


def fix_path(x):
    return os.path.split(x)[1]


def display_date(x):
    if isinstance(x, datetime.datetime):
        return x.date().isoformat()
    return x.isoformat()


jinja_env.globals.update({
    'id_type': id_type,
    'fix_id': fix_id,
    'abs': abs_string,
    'value_from_cents': value_from_cents,
    'get_total': get_total,
    'today': datetime.date.today,
    'PaymentFormat': PaymentFormat,
    'fix_path': fix_path,
    'display_date': display_date,
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
