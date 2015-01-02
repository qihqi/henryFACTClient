import json

from bottle import Bottle, response, request, abort

from henry.layer2.productos import Transferencia
from henry.helpers.serialization import json_dump
from henry.config import prodapi, transapi, dbcontext

bodega_api_app = Bottle()


@bodega_api_app.get('/api/alm/<almacen_id>/producto/<prod_id>')
@dbcontext
def get_prod_from_inv(almacen_id, prod_id):
    prod = prodapi.get_producto(prod_id=prod_id, almacen_id=almacen_id)
    if prod is None:
        response.status = 404
    return json_dump(prod)


@bodega_api_app.get('/api/producto/<prod_id>')
@dbcontext
def get_prod(prod_id):
    return get_prod_from_inv(None, prod_id)


@bodega_api_app.get('/api/producto')
@dbcontext
def search_prod():
    prefijo = request.query.prefijo
    if prefijo:
        return json_dump(list(prodapi.search_producto(prefix=prefijo)))
    else:
        response.status = 400
        return None


@bodega_api_app.get('/api/alm/<almacen_id>/producto')
@dbcontext
def search_prod_alm(almacen_id):
    prefijo = request.query.prefijo
    if prefijo:
        return json_dump(list(prodapi.search(prefix=prefijo,
                                             almacen_id=almacen_id)))
    else:
        response.status = 400
        return None


@bodega_api_app.post('/api/ingreso')
@dbcontext
def crear_ingreso():
    json_content = request.body.read()
    content = json.loads(json_content)
    ingreso = Transferencia.deserialize(content)
    codigo = transapi.create(ingreso)
    return {'codigo': codigo}


@bodega_api_app.put('/api/ingreso/<ingreso_id>')
@dbcontext
def postear_ingreso(ingreso_id):
    t = transapi.commit(uid=ingreso_id)
    return {'status': t.meta.status}


@bodega_api_app.delete('/api/ingreso/<ingreso_id>')
@dbcontext
def delete_ingreso(ingreso_id):
    t = transapi.delete(uid=ingreso_id)
    return {'status': t.meta.status}


@bodega_api_app.get('/api/ingreso/<ingreso_id>')
@dbcontext
def get_ingreso(ingreso_id):
    ing = transapi.get_doc(ingreso_id)
    if ing is None:
        abort(404, 'Ingreso No encontrada')
        return
    return json_dump(ing.serialize())
