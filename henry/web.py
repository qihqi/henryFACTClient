from bottle import Bottle

from henry.coreconfig import (dbcontext, auth_decorator)
from henry.config import jinja_env

webmain = w = Bottle()


@w.get('/app')
@dbcontext
@auth_decorator(0)
def index():
    return jinja_env.get_template('base.html').render()
