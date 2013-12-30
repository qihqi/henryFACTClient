import json
import sys
import bottle
from bottle import run, request
from bottle import get, post, put, HTTPError
from config import get_engine
from henry.layer1.api import get_product_by_id, create_producto, search_product
from henry.helpers.connection import timed

app = bottle.Bottle()

class Response(object):
    def __init__(self, result=None, error=None, continuation=None):
        self.result = result
        self.error = error
        self.success = error is None
        self.cont = continuation

    def serialize(self):
        data = {'success': self.success}
        if self.error:
            data['error'] = self.error
        if self.result:
            data['result'] = self.result
        if self.cont:
            data['cont'] = self.cont
        return json.dumps(data)


@app.get('/api/producto')
def get_producto():
    prod_id = request.query.get('id')
    bodega_id = request.query.get('bodega_id')
    if prod_id:
        prod, cont = get_product_by_id(prod_id, bodega_id)
        return Response(result=_display_prod(prod, cont)).serialize()
    prefijo = request.query.get('prefijo')
    if prefijo:
        result = []
        for prod, cont in search_product(prefijo):
            result.append(_display_prod(prod, cont))
        return Response(result).serialize()

    raise HTTPError()


def _display_prod(prod, cont):
    return {
        'codigo': prod.codigo,
        'nombre': prod.nombre,
        'precio1': int(cont.precio * 100),
        'precio2': int(cont.precio * 100),
        'threshold': cont.cant_mayorista,
    }


@app.get('/api/cliente')
def get_cliente():
    cliente_id = request.query.get('id')
    if cliente_id:
        return {
            'cliente_id': cliente_id,
            'nombres': 'x x',
            'apellidos': 'y y',
            'direccion': 'direccion',
            'telefono': 'tel'
        }

@app.get('/api/pedido')
def get_nota_de_pedido():
    pass


@app.put('/api/pedido')
def put_nota_de_pedido():
    pass


@app.put('/api/factura')
def put_factura():
    pass


def setup_testdata():
    create_producto('0', 'prueba 0', 0.2, 0.1, 0)
    create_producto('1', 'prueba 1', 0.2, 0.1, 0)
    create_producto('2', 'prueba 2', 0.2, 0.1, 0)
    create_producto('3', 'prueba 3', 0.2, 0.1, 0)
    create_producto('4', 'prueba 4', 0.2, 0.1, 0)
    create_producto('5', 'prueba 5', 0.2, 0.1, 0)
    create_producto('6', 'prueba 6', 0.2, 0.1, 0)


if __name__ == '__main__':
    from henry.layer1.schema import Base
    Base.metadata.create_all(get_engine)
    setup_testdata()
    run(host='localhost', debug=True, port=8080)



