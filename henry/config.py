import datetime
import os

from jinja2 import Environment, FileSystemLoader

from henry.base.fileservice import FileService
from henry.base.dbapi import DBApi
from henry.constants import (
    INGRESO_PATH, BEAKER_DIR,
    EXTERNAL_URL, EXTERNAL_USER, EXTERNAL_PASS,
    IMAGE_PATH, EXTERNAL_AUTH_URL, TEMPLATE_LOCATION)

from henry.accounting.dao import Image, Todo

from henry.dao.productos import (
    RevisionApi, ProdCount, Product, Bodega, Category, ProdApi, ProdItemGroup)
from henry.dao.document import DocumentApi
from henry.dao.inventory import Transferencia
from henry.invoice.dao import PaymentFormat
from henry.environments import make_jinja_env
from henry.misc import id_type, fix_id, abs_string, value_from_cents, get_total
from henry.externalapi import ExternalApi
from henry.coreconfig import (sessionmanager, transactionapi, priceapi,
                              storeapi)

sm = sessionmanager
countapi = DBApi(sessionmanager, ProdCount)
revisionapi = RevisionApi(sessionmanager, countapi, transactionapi)
# paymentapi = PaymentApi(sessionmanager)
paymentapi = None
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
                               EXTERNAL_USER, EXTERNAL_PASS,
                               EXTERNAL_AUTH_URL)



# imgserver = ImageServer('/app/img', DBApi(sm, Image), imagefiles)
imgserver = None
todoapi = DBApi(sm, Todo)


jinja_env = make_jinja_env(TEMPLATE_LOCATION)

BEAKER_SESSION_OPTS = {
    'session.type': 'file',
    'session.cookie_expires': False,
    'session.data_dir': BEAKER_DIR,
    'session.auto': True
}


BODEGAS_EXTERNAS = (
    ('POLICENTRO', externaltransapi, 1),  # nombre, api, numero de bodega
)
