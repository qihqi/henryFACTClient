from beaker.middleware import SessionMiddleware
from henry.config import BEAKER_SESSION_OPTS
from henry.constants import INVOICE_MODE
from henry.api import get_master, get_slave

api_factory = get_master
if INVOICE_MODE == 'slave':
    api_factory = get_slave
application = SessionMiddleware(api_factory(), BEAKER_SESSION_OPTS)
