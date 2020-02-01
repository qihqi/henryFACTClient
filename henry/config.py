from henry.base.fileservice import FileService
from henry.constants import (INGRESO_PATH, BEAKER_DIR, IMAGE_PATH, TEMPLATE_LOCATION)

from henry.coreconfig import sessionmanager, transactionapi

from henry.dao.document import DocumentApi
from henry.inventory.dao import Transferencia
from henry.environments import make_jinja_env

sm = sessionmanager

imagefiles = FileService(IMAGE_PATH)
transapi = DocumentApi(sessionmanager, FileService(INGRESO_PATH),
                       transactionapi, object_cls=Transferencia)


jinja_env = make_jinja_env(TEMPLATE_LOCATION)

BEAKER_SESSION_OPTS = {
    'session.type': 'file',
    'session.cookie_expires': False,
    'session.data_dir': BEAKER_DIR,
    'session.auto': True
}

