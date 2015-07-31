from bottle import Bottle, response, request, abort

from henry.base.schema import NPriceList
from henry.config import (prodapi, dbcontext, clientapi,
                          auth_decorator, pedidoapi, sessionmanager,
                          actionlogged)
from henry.base.serialization import json_dumps, json_loads
from henry.dao import Client

api = Bottle()


# ######### PRODUCT ########################
@api.get('/api/alm/<almacen_id>/producto/<prod_id:path>')
@dbcontext
@actionlogged
def get_prod_from_inv(almacen_id, prod_id):
    print prod_id
    prod = prodapi.get_producto(prod_id, almacen_id)
    if prod is None:
        response.status = 404
    use_thousandth = request.query.get('use_thousandth', '1')
    if int(use_thousandth) and prod.threshold:
        prod.threshold *= 1000
    return json_dumps(prod)


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


@api.get('/api/producto')
@dbcontext
@actionlogged
def search_prod():
    prefijo = request.query.prefijo
    if prefijo:
        return json_dumps(list(prodapi.search_producto(prefix=prefijo)))
    response.status = 400
    return None


@api.get('/api/alm/<almacen_id>/producto')
@dbcontext
@actionlogged
def search_prod_alm(almacen_id):
    prefijo = request.query.prefijo
    if prefijo:
        result = list(prodapi.search_producto(
            prefix=prefijo,
            almacen_id=almacen_id))
        use_thousandth = request.query.get('use_thousandth', 1)
        if int(use_thousandth):
            for x in result:
                if x.threshold:
                    x.threshold *= 1000
        return json_dumps(result)
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


# ################ CLIENT ############################
@api.get('/api/cliente/<codigo>')
@dbcontext
@actionlogged
def get_cliente(codigo):
    client = clientapi.get(codigo)
    if client is None:
        abort(404, 'cliente no encontrado')
    return client.to_json()


@api.put('/api/cliente/<codigo>')
@dbcontext
@auth_decorator
@actionlogged
def update_client(codigo):
    client_dict = json_loads(request.body.read())
    clientapi.update(codigo, client_dict)


@api.post('/api/cliente/<codigo>')
@dbcontext
@auth_decorator
@actionlogged
def create_client(codigo):
    client = Client.deserialize(json_loads(request.body.read()))
    client.codigo = codigo
    clientapi.create(client)


@api.get('/api/cliente')
@dbcontext
@actionlogged
def search_client():
    prefijo = request.query.prefijo
    if prefijo:
        return json_dumps(list(clientapi.search(apellido=prefijo)))
    response.status = 400
    return None


# ####################### PEDIDO ############################
@api.post('/api/pedido')
@dbcontext
@auth_decorator
@actionlogged
def save_pedido():
    json_content = request.body.read()
    uid, _ = pedidoapi.save(json_content)
    return {'codigo': uid}


@api.get('/api/pedido/<uid>')
@actionlogged
def get_pedido(uid):
    f = pedidoapi.get_doc(uid)
    if f is None:
        response.status = 404
    return f


from henry.authentication import app
api.merge(app)
