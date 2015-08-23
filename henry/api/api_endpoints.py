from bottle import Bottle, response, request, abort
import datetime
from henry.base.auth import get_user

from henry.bottlehelper import get_property_or_fail
from henry.schema.meta import NComment
from henry.schema.inventory import NContenido
from henry.schema.core import NPriceList
from henry.config import (prodapi, dbcontext, clientapi,
                          auth_decorator, pedidoapi, sessionmanager,
                          actionlogged, priceapi)
from henry.base.serialization import json_dumps, json_loads
from henry.dao import Client

api = Bottle()

# ######### PRODUCT ########################

@api.get('/api/producto/<prod_id:path>')
@dbcontext
@actionlogged
def get_prod(prod_id):
    options = request.query.options
    if options == 'all':
        result = prodapi.get_producto_full(prod_id)
        result_dict = result.serialize()
        result_dict['precios'] = [
            (x.almacen_id, x.almacen_name, x.precio1, x.precio2, x.threshold)
            for x in result.precios]
        return json_dumps(result_dict)

    prod = prodapi.get_producto(prod_id=prod_id)
    if prod is None:
        response.status = 404
    return json_dumps(prod)

@api.get('/api/bod/<bodega_id>/producto/<prod_id:path>')
@dbcontext
@actionlogged
def get_prod_cant(bodega_id, prod_id):
    prod = prodapi.get_cant(prod_id, bodega_id)
    if prod is None:
        response.status = 404
    return json_dumps(prod)

@api.get('/api/bod/<bodega_id>/producto')
@dbcontext
@actionlogged
def search_prod_cant(bodega_id):
    prefix = request.query.prefijo
    if prefix:
        prod = list(prodapi.get_cant_prefix(prefix, bodega_id))
        return json_dumps(prod)
    response.status = 400
    return None


@api.put('/api/bod/<bodega_id>/producto/<prod_id:path>')
@dbcontext
@actionlogged
def toggle_inactive(bodega_id, prod_id):
    inactive = json_loads(request.body.read())['inactivo']
    sessionmanager.session.query(NContenido).filter_by(
        bodega_id=bodega_id, prod_id=prod_id).update(
        {NContenido.inactivo: inactive})
    sessionmanager.session.commit()
    return {'inactivo': inactive}


@api.get('/api/producto')
@dbcontext
@actionlogged
def search_prod():
    prefijo = request.query.prefijo
    if prefijo:
        return json_dumps(list(prodapi.search_producto(prefix=prefijo)))
    response.status = 400
    return None




@api.put('/api/producto/<pid>')
@dbcontext
@auth_decorator
@actionlogged
def crear_producto(pid):
    content = json_loads(request.body.read())
    prodapi.update_prod(pid, content)


@api.put('/api/alm/<alm_id:int>/producto/<pid:path>')
@dbcontext
@auth_decorator
@actionlogged
def update_price(alm_id, pid):
    content = json_loads(request.body.read())
    if not content:
        abort(400)
    prodapi.update_or_create_price(alm_id, pid, content)


@api.delete('/api/alm/<alm_id>/producto/<pid:path>')
@dbcontext
@auth_decorator
@actionlogged
def delete_price(alm_id, pid):
    session = sessionmanager.session
    count = session.query(NPriceList).filter_by(
        almacen_id=alm_id, prod_id=pid).delete()
    return {'deleted': count}


@api.post('/api/comment')
@dbcontext
@auth_decorator
@actionlogged
def post_comment():
    comment = json_loads(request.body.read())
    c = NComment()
    c.objid = comment['objid']
    c.objtype = comment['objtype']
    c.user_id = get_user(request)['username']
    c.timestamp = datetime.datetime.now()
    c.comment = comment['comment']
    sessionmanager.session.add(c)
    sessionmanager.session.commit()
    return {'comment': c.uid}
