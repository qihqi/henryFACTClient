from bottle import Bottle


def make_wsgi_app():
    app = Bottle()
    return app
