from bottle import Bottle, response, request

from henry.layer2.models import Producto
from henry.helpers.serialization import json_dump

bodega_api_app = Bottle()

@bodega_api_app.get('/api/bodega/<bodega_id>/producto/<prod_id>')
def get_prod_from_inv(bodega_id, prod_id):
    return json_dump(Producto.get(prod_id, bodega_id))


@bodega_api_app.get('/api/bodega/<bodega_id>/producto')
def search_prod(bodega_id):
    prefijo = request.query.get('prefijo')
    if prefijo:
        return json_dump(list(Producto.search(prefijo, bodega_id)))
    else:
        response.status = 400


@bodega_api_app.put('/api/bodega/<bodega_id>/ingreso')
def crear_ingreso(bodega_id):
    pass


@bodega_api_app.post('/api/bodega/<bodega_id>/ingreso/<ingreso_id>')
def postear_ingreso(bodega_id, ingreso_id):
    pass


