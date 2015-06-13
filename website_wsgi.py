from beaker.middleware import SessionMiddleware
from henry.config import BEAKER_SESSION_OPTS
from henry.server import app

application = SessionMiddleware(app, BEAKER_SESSION_OPTS)
