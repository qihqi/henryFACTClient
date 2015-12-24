import bottle
from PIL import Image as PilImage
from henry.accounting.dao import ImageServer, Image, PaymentApi

from henry.accounting.web import make_wsgi_app
from henry.base.dbapi import DBApiGeneric, DBApi
from henry.config import imgserver, jinja_env, imagefiles, sm
from henry.coreconfig import dbcontext, sessionmanager, auth_decorator

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

bottle.run(app)
