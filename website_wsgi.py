from beaker.middleware import SessionMiddleware
from henry.config import BEAKER_SESSION_OPTS
from henry.server import app
from henry.api.api_endpoints import api

app.merge(api)
application = SessionMiddleware(app, BEAKER_SESSION_OPTS)
