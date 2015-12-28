import bottle
import json
from henry.base.serialization import json_dumps


class RestApi(object):

    def __init__(self, dbapi, clazz):
        self.dbapi = dbapi
        self.clazz = clazz

    def get(self, pkey):
        with self.dbapi.session:
            return json_dumps(self.dbapi.get(pkey, self.clazz).serialize())

    def put(self, pkey):
        content_dict = json.loads(bottle.request.body.read())
        with self.dbapi.session:
            obj = self.clazz()
            setattr(obj, self.clazz.pkey.name, pkey)
            count = self.dbapi.update(obj, content_dict=content_dict)
            return {'modified': count}

    def post(self):
        content_dict = json.loads(bottle.request.body.read())
        with self.dbapi.session:
            obj = self.clazz()
            obj.merge_from(content_dict)
            pkey = self.dbapi.create(obj)
            return {'key': pkey}

    def delete(self, pkey):
        with self.dbapi.session:
            obj = self.clazz()
            setattr(obj, self.clazz.pkey.name, pkey)
            count = self.dbapi.delete(obj)
            return {'deleted': count}

    def search(self):
        with self.dbapi.session:
            args = bottle.request.query
            content = self.dbapi.search(self.clazz, **args)
            return {'result': [c.serialize() for c in content]}


def bind_dbapi_rest(url, dbapi, clazz, app):
    restapi = RestApi(dbapi, clazz)
    url_with_id = url + '/<pkey>'
    app.get(url_with_id)(restapi.get)
    app.put(url_with_id)(restapi.put)
    app.delete(url_with_id)(restapi.delete)
    app.post(url)(restapi.post)
    app.get(url)(restapi.search)
    return app
