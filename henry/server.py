import sys
import os

from bottle import run, static_file, Bottle
from beaker.middleware import SessionMiddleware

from henry.constants import BEAKER_DIR
from henry.api_endpoints import api
from henry.website.web_inventory import web_inventory_webapp
from henry.website.accounting import accounting_webapp
from henry.authentication import app as authapp

app = Bottle()


@app.get('/static/<rest:path>')
def static(rest):
    return static_file(rest, root='./static/')


app.merge(api)
app.merge(web_inventory_webapp)
app.merge(accounting_webapp)
app.merge(authapp)
session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 300,
    'session.data_dir': BEAKER_DIR,
    'session.auto': True
}

app = SessionMiddleware(app, session_opts)


def main():
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    from henry.base.schema import Base
    from henry.config import engine

    print 'i am here '
    Base.metadata.create_all(engine)
    # setup_testdata()
    # print get_cliente_by_id('NA')
    #  print json.dumps(Venta.get(86590).serialize(), cls=ModelEncoder)
    host, port = '0.0.0.0', 8080
    if len(sys.argv) > 1:
        url = sys.argv[1]
        host, port = url.split(':')
        port = int(port)
    run(app, host=host, debug=True, port=port)
    return 'http://localhost:8080'


if __name__ == '__main__':
    main()
