from bottle import Bottle, response, request

from henry.layer2.productos import Product, ProductApiDB, TransApiDB
from henry.helpers.serialization import json_dump
from henry.config import prodapi, transapi

bodega_api_app = Bottle()

@bodega_api_app.get('/api/alm/<almacen_id>/producto/<prod_id>')
def get_prod_from_inv(almacen_id, prod_id):
    prod = prodapi.get_producto(prod_id=prod_id, almacen_id=almacen_id)
    if prod is None:
        response.status = 404
    return json_dump(prod)


@bodega_api_app.get('/api/producto/<prod_id>')
def get_prod(prod_id):
    return json_dump(prodapi.get_producto(prod_id=prod_id))


@bodega_api_app.get('/api/producto')
def search_prod(almacen_id):
    prefijo = request.query.prefijo
    if prefijo:
        return json_dump(list(prodapi.search(prefix=prefijo)))
    else:
        response.status = 400
        return None


@bodega_api_app.get('/api/alm/<almacen_id>/producto')
def search_prod(almacen_id):
    prefijo = request.query.prefijo
    if prefijo:
        return json_dump(list(prodapi.search(prefix=prefijo, almacen_id=almacen_id)))
    else:
        response.status = 400
        return None


@bodega_api_app.post('/api/bodega/<bodega_id>/ingreso')
def crear_ingreso(bodega_id):
    json_content = request.body.read()
    content = json.parse(json_content)
    ingreso = Transferencia.deserialize(content)
    codigo = transapi.create(ingreso)
    return {'codigo': codigo} 


@bodega_api_app.put('/api/bodega/<bodega_id>/ingreso/<ingreso_id>')
def postear_ingreso(bodega_id, ingreso_id):
    t = transapi.commit(Transferencia(uid=ingreso_id))
    return t.serialize()

