import datetime
from bottle import Bottle, request

from henry.coreconfig import (dbcontext, auth_decorator)
from henry.config import jinja_env
from henry.dao.document import Status

webmain = w = Bottle()


@w.get('/app')
@dbcontext
@auth_decorator(0)
def index():
    return jinja_env.get_template('base.html').render()
