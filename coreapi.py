from henry.api.coreapi import api
from beaker.middleware import SessionMiddleware
from henry.coreconfig import BEAKER_SESSION_OPTS

application = SessionMiddleware(api, BEAKER_SESSION_OPTS)
import bottle
bottle.run(application)
