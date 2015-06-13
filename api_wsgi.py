from beaker.middleware import SessionMiddleware
from henry.config import BEAKER_SESSION_OPTS
from henry.api_endpoints import api

application = SessionMiddleware(api, BEAKER_SESSION_OPTS)
