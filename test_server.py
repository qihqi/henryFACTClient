from __future__ import print_function
import sys
import os

from bottle import run, static_file, Bottle, install
from henry.config import BEAKER_SESSION_OPTS

app = Bottle()


@app.get('/static/<rest:path>')
def static(rest):
    return static_file(rest, root='./static/')


def main():
    global app
    from beaker.middleware import SessionMiddleware
    import coreapi
    import website_wsgi
    import cloud_inv
    app.merge(coreapi.api)
    app.merge(website_wsgi.app)
    app.merge(cloud_inv.api)
    app = SessionMiddleware(app, BEAKER_SESSION_OPTS)
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    from henry.schema.base import Base
    from henry.coreconfig import engine

    Base.metadata.create_all(engine)
    host, port = '0.0.0.0', 8080
    if len(sys.argv) > 1:
        url = sys.argv[1]
        host, port = url.split(':')
        port = int(port)
    for r in app.app.routes:
        print(r.method, r.rule)
    run(app, host=host, debug=True, port=port)
    return 'http://localhost:8080'


if __name__ == '__main__':
    main()
