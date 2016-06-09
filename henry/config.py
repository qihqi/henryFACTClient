from henry.base.fileservice import FileService
from henry.base.dbapi import DBApi
from henry.constants import (
    INGRESO_PATH, BEAKER_DIR,
    EXTERNAL_URL, EXTERNAL_USER, EXTERNAL_PASS,
    IMAGE_PATH, EXTERNAL_AUTH_URL, TEMPLATE_LOCATION)

from henry.coreconfig import sessionmanager, transactionapi

from henry.dao.document import DocumentApi
from henry.inventory.dao import Transferencia
from henry.environments import make_jinja_env
from henry.externalapi import ExternalApi

sm = sessionmanager

# paymentapi = PaymentApi(sessionmanager)
paymentapi = None
imagefiles = FileService(IMAGE_PATH)
transapi = DocumentApi(sessionmanager, FileService(INGRESO_PATH),
                       transactionapi, object_cls=Transferencia)
externaltransapi = ExternalApi(EXTERNAL_URL, 'ingreso',
                               EXTERNAL_USER, EXTERNAL_PASS,
                               EXTERNAL_AUTH_URL)



# imgserver = ImageServer('/app/img', DBApi(sm, Image), imagefiles)
imgserver = None


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
