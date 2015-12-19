import bottle
import json

class RestApi(object):

    def __init__(self, dbapi, sessionmanager):
        self.dbapi = dbapi
        self.sm = sessionmanager

    def get(self, pkey):
        with self.sm as session:
            return self.dbapi.get(session, pkey=pkey).serialize()

    def put(self, pkey):
        content_dict = json.loads(bottle.request.body.read())
        with self.sm as session:
            count = self.dbapi.update(session,
                                      pkey=pkey, content_dict=content_dict)
            return {'modified': count}

    def post(self):
        content_dict = json.loads(bottle.request.body.read())
        with self.sm as session:
            pkey = self.dbapi.create(session, content_dict=content_dict)
            return {'key': pkey}

    def delete(self, pkey):
        with self.sm as session:
            count = self.dbapi.delete(session, pkey)
            return {'deleted': count}

    def search(self):
        with self.sm as session:
            args = bottle.request.query
            content = self.dbapi.search(session, **args)
            return {'result': [c.serialize() for c in content]}


def bind_dbapi_rest(url, dbapi, sessionmanager, app):
    restapi = RestApi(dbapi, sessionmanager)
    url_with_id = url + '/<pkey>'
    app.get(url_with_id)(restapi.get)
    app.put(url_with_id)(restapi.put)
    app.delete(url_with_id)(restapi.delete)
    app.post(url)(restapi.post)
    app.get(url)(restapi.search)
    return app
