import json
import bottle
import sys
from bottle import run, request
from bottle import HTTPError
from henry.layer2.models import Producto, Venta, Cliente
from henry.layer1.api import  get_nota_de_venta_by_id, get_cliente_by_id, save_nota, get_items_de_venta_by_id
from henry.config import CONFIG, get_engine
from henry.helpers.serialization import ModelEncoder

app = bottle.Bottle()


class Response(object):
    def __init__(self, result=None, error=None, continuation=None):
        self.result = result
        self.error = error
        self.success = error is None
        self.cont = continuation

    def serialize(self):
        data = {'success': self.success, 'result': self.result}
        if self.error:
            data['error'] = self.error
        if self.cont:
            data['cont'] = self.cont
        return json.dumps(self.result, cls=ModelEncoder)


@app.get('/api/producto')
def get_producto():
    prod_id = request.query.get('id')
    bodega_id = int(request.query.get('bodega_id'))
    if prod_id:
        result = Producto.get(prod_id, bodega_id)
        resp = Response(result=result).serialize()
        return resp
    prefijo = request.query.get('prefijo')
    if prefijo:
        result = list(Producto.search(prefijo, bodega_id))
        return Response(result).serialize()

    raise HTTPError()


def _display_prod(cont):
    return {
        'codigo': cont.prod_id.decode('latin1'),
        'nombre': cont.producto.nombre.decode('latin1'),
        'precio1': int(cont.precio * 100),
        'precio2': int(cont.precio * 100),
        'threshold': cont.cant_mayorista,
    }


@app.get('/api/cliente')
def get_cliente():
    cliente_id = request.query.get('id')
    if cliente_id:
        return json.dumps(Cliente.get(cliente_id), cls=ModelEncoder)

    prefijo = request.query.get('prefijo')
    if prefijo:
        return json.dumps(Cliente.search(prefijo), cls=ModelEncoder)

@app.get('/api/pedido')
def get_nota_de_pedido():
    codigo = request.query.get('id')
    if codigo:
        venta = Venta.get(codigo)
        return Response(result=venta).serialize()


@app.put('/api/pedido')
def put_nota_de_pedido():
    data = json.loads(request.body.read())
    num = save_nota(data)
    return {'num': num}



@app.put('/api/factura')
def put_factura():
    data = request.body.read()
    print data



def main():
    import sys
    import os
    CONFIG['echo'] = True
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    from henry.layer1.schema import Base
    Base.metadata.create_all(get_engine())
    #setup_testdata()
    #print get_cliente_by_id('NA')
  #  print json.dumps(Venta.get(86590).serialize(), cls=ModelEncoder)
    run(app, host='localhost', debug=True, port=8080)
    return 'http://localhost:8080'


if __name__ == '__main__':
    main()



