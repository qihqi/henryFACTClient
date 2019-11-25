from __future__ import print_function
from builtins import object
import sys
import bottle
import json
from henry.base.serialization import json_dumps


class RestApi(object):

    def __init__(self, dbapi, clazz, logging=None):
        self.dbapi = dbapi
        self.clazz = clazz
        self.logging = logging

    def get(self, pkey):
        with self.dbapi.session:
            return json_dumps(self.dbapi.get(pkey, self.clazz).serialize())

    def put(self, pkey):
        content_dict = json.loads(bottle.request.body.read())

        with self.dbapi.session:
            try:
                if self.logging:
                    old_obj = self.dbapi.get(pkey, self.clazz).serialize()
                    self.logging(self.clazz, 'put', old_obj, content_dict)
            except Exception as e:
                print(e, file=sys.stderr)
                print('logging failed', file=sys.stderr)
            obj = self.clazz()
            setattr(obj, self.clazz.pkey.name, pkey)
            count = self.dbapi.update(obj, content_dict=content_dict)
            return json_dumps({'modified': count})

    def post(self):
        content_dict = json.loads(bottle.request.body.read())
        with self.dbapi.session:
            obj = self.clazz()
            obj.merge_from(content_dict)
            pkey = self.dbapi.create(obj)
            return json_dumps({'key': pkey})

    def delete(self, pkey):
        with self.dbapi.session:
            obj = self.clazz()
            setattr(obj, self.clazz.pkey.name, pkey)
            count = self.dbapi.delete(obj)
            return json_dumps({'deleted': count})

    def search(self):
        with self.dbapi.session:
            args = bottle.request.query
            content = self.dbapi.search(self.clazz, **args)
            return json_dumps({'result': [c.serialize() for c in content]})


def bind_restapi(url, restapi, app, skips_method=()):
    url_with_id = url + '/<pkey>'
    if 'GET' not in skips_method:
        app.get(url_with_id)(restapi.get)
        app.get(url)(restapi.search)
    if 'PUT' not in skips_method:
        app.put(url_with_id)(restapi.put)
    if 'DELETE' not in skips_method:
        app.delete(url_with_id)(restapi.delete)
    if 'POST' not in skips_method:
        app.post(url)(restapi.post)
    return app


def bind_dbapi_rest(url, dbapi, clazz, app, skips_method=()):
    restapi = RestApi(dbapi, clazz)
    return bind_restapi(url, restapi, app, skips_method)
