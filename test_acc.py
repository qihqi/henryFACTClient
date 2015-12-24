import bottle
from PIL import Image as PilImage
from henry.accounting.dao import ImageServer, Image, PaymentApi

from henry.accounting.web import make_wsgi_app, make_wsgi_api
from henry.base.dbapi import DBApiGeneric, DBApi
from henry.config import imgserver, jinja_env, imagefiles, sm
from henry.coreconfig import dbcontext, sessionmanager, auth_decorator, invapi

dbapi = DBApiGeneric(sessionmanager=sessionmanager)
paymentapi = PaymentApi(sessionmanager=sessionmanager)


def save_image(imgfile, size, filename):
    im = PilImage.open(imgfile)
    if im.size[0] > size[0]:
        im.resize(size)
    im.save(filename)

imgserver = ImageServer('/app/img', DBApi(sm, Image), imagefiles, save_image)
app = make_wsgi_app(dbcontext, imgserver,
                    dbapi, paymentapi, jinja_env, auth_decorator, imagefiles)
api = make_wsgi_api(dbapi=dbapi, dbcontext=dbcontext, paymentapi=paymentapi,
                    auth_decorator=auth_decorator, invapi=invapi)

if __name__ == '__main__':
    import bottle
    @api.get('/static/<rest:path>')
    def static(rest):
        return bottle.static_file(rest, root='./static/')
    bottle.run(app)
