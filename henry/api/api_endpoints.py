from bottle import Bottle, response, request, abort
import datetime
from henry.base.auth import get_user

from henry.bottlehelper import get_property_or_fail
from henry.schema.meta import NComment
from henry.schema.prod import NContenido, NPriceList
from henry.coreconfig import (dbcontext, invapi,
                          auth_decorator, sessionmanager,
                          actionlogged)
from henry.config import prodapi, revisionapi, transapi
from henry.base.serialization import json_dumps, json_loads
from henry.dao.inventory import Transferencia

api = Bottle()


# ######### PRODUCT ########################
@api.get('/app/api/producto/<prod_id:path>')
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

    prod = prodapi.prod.get(prod_id)
    if prod is None:
        response.status = 404
    return json_dumps(prod)


@api.get('/app/api/bod/<bodega_id>/producto/<prod_id:path>')
@dbcontext
@actionlogged
def get_prod_cant(bodega_id, prod_id):
    prod = list(prodapi.count.search(prod_id=prod_id, bodega_id=bodega_id))
    if not prod:
        response.status = 404
    prod = prod[0]
    prod_dict = prod.serialize()
    prod_dict['nombre'] = prodapi.prod.getone(codigo=prod_id).nombre
    return json_dumps(prod_dict)


@api.get('/app/api/bod/<bodega_id>/producto')
@dbcontext
@actionlogged
def search_prod_cant(bodega_id):
    prefix = get_property_or_fail(request.query, 'prefijo')
    prod = list(prodapi.get_cant_prefix(prefix, bodega_id))
    return json_dumps(prod)


@api.put('/app/api/bod/<bodega_id>/producto/<prod_id:path>')
@dbcontext
@actionlogged
def toggle_inactive(bodega_id, prod_id):
    inactive = json_loads(request.body.read())['inactivo']
    sessionmanager.session.query(NContenido).filter_by(
        bodega_id=bodega_id, prod_id=prod_id).update(
        {NContenido.inactivo: inactive})
    sessionmanager.session.commit()
    return {'inactivo': inactive}


@api.get('/app/api/producto')
@dbcontext
@actionlogged
def search_prod():
    prefijo = request.query.prefijo
    if prefijo:
        return json_dumps(list(
            prodapi.prod.search(**{'nombre-prefix': prefijo})))
    response.status = 400
    return None


@api.put('/app/api/producto/<pid>')
@dbcontext
@auth_decorator
@actionlogged
def crear_producto(pid):
    content = json_loads(request.body.read())
    prodapi.update_prod(pid, content)


@api.post('/app/api/comment')
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


@api.get('/app/api/nota')
@dbcontext
@actionlogged
def get_invoice_by_date():
    start = request.query.get('start_date')
    end = request.query.get('end_date')
    if start is None or end is None:
        abort(400, 'invalid input')
    datestrp = datetime.datetime.strptime
    start_date = datestrp(start, "%Y-%m-%d")
    end_date = datestrp(end, "%Y-%m-%d")
    status = request.query.get('status')
    result = invapi.search_metadata_by_date_range(start_date, end_date, status)
    return json_dumps(list(result))


# ################# INGRESO ###########################3
@api.post('/app/api/ingreso')
@dbcontext
@auth_decorator
@actionlogged
def crear_ingreso():
    json_content = request.body.read()
    json_dict = json_loads(json_content)
    ingreso = Transferencia.deserialize(json_dict)
    ingreso = transapi.save(ingreso)
    return {'codigo': ingreso.meta.uid}


@api.put('/app/api/ingreso/<ingreso_id>')
@dbcontext
@auth_decorator
@actionlogged
def postear_ingreso(ingreso_id):
    trans = transapi.get_doc(ingreso_id)
    transapi.commit(trans)
    return {'status': trans.meta.status}


@api.delete('/app/api/ingreso/<ingreso_id>')
@dbcontext
@actionlogged
def delete_ingreso(ingreso_id):
    trans = transapi.get_doc(ingreso_id)
    transapi.delete(trans)
    return {'status': trans.meta.status}


@api.get('/app/api/ingreso/<ingreso_id>')
@dbcontext
@actionlogged
def get_ingreso(ingreso_id):
    ing = transapi.get_doc(ingreso_id)
    if ing is None:
        abort(404, 'Ingreso No encontrada')
        return
    return json_dumps(ing.serialize())


@api.put('/app/api/revision/<rid>')
@dbcontext
@auth_decorator
@actionlogged
def put_revision(rid):
    if revisionapi.commit(rid):
        return {'status': 'AJUSTADO'}
    abort(404)
