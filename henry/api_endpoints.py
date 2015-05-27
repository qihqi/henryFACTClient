import json
from decimal import Decimal

from bottle import Bottle, response, request, abort

from henry.layer1.schema import NUsuario
from henry.config import (prodapi, transapi, dbcontext, clientapi,
                          invapi, auth_decorator, pedidoapi, sessionmanager)
from henry.helpers.serialization import json_dump, json_loads
from henry.dao import Client, Invoice, Transferencia
from henry.authentication import get_session

api = Bottle()


@api.get('/api/alm/<almacen_id>/producto/<prod_id>')
@dbcontext
def get_prod_from_inv(almacen_id, prod_id):
    prod = prodapi.get_producto(prod_id=prod_id, almacen_id=almacen_id)
    if prod is None:
        response.status = 404
    return json_dump(prod)


@api.get('/api/producto/<prod_id>')
@dbcontext
def get_prod(prod_id):
    return get_prod_from_inv(None, prod_id)


@api.get('/api/producto')
@dbcontext
def search_prod():
    prefijo = request.query.prefijo
    if prefijo:
        return json_dump(list(prodapi.search_producto(prefix=prefijo)))
    else:
        response.status = 400
        return None


@api.get('/api/alm/<almacen_id>/producto')
@dbcontext
def search_prod_alm(almacen_id):
    prefijo = request.query.prefijo
    if prefijo:
        return json_dump(
            list(prodapi.search_producto(
                prefix=prefijo,
                almacen_id=almacen_id)))
    else:
        response.status = 400
        return None


@api.post('/api/ingreso')
@auth_decorator
@dbcontext
def crear_ingreso():
    json_content = request.body.read()
    content = json_loads(json_content)
    ingreso = Transferencia.deserialize(content)
    codigo = transapi.create(ingreso)
    return {'codigo': codigo}


@api.put('/api/ingreso/<ingreso_id>')
@auth_decorator
@dbcontext
def postear_ingreso(ingreso_id):
    t = transapi.commit(uid=ingreso_id)
    return {'status': t.meta.status}


@api.delete('/api/ingreso/<ingreso_id>')
@dbcontext
def delete_ingreso(ingreso_id):
    t = transapi.delete(uid=ingreso_id)
    return {'status': t.meta.status}


@api.get('/api/ingreso/<ingreso_id>')
@dbcontext
def get_ingreso(ingreso_id):
    ing = transapi.get_doc(ingreso_id)
    if ing is None:
        abort(404, 'Ingreso No encontrada')
        return
    return json_dump(ing.serialize())


@api.get('/api/cliente/<codigo>')
@dbcontext
def get_cliente(codigo):
    client = clientapi.get(codigo)
    if client is None:
        abort(404, 'cliente no encontrado')
    return client.to_json()


@api.put('/api/cliente/<codigo>')
@auth_decorator
@dbcontext
def update_client(codigo):
    client_dict = json.parse(request.body)
    client = Client.deserialize(client_dict)
    clientapi.save(client)
    return {'codigo': client.codigo}


@api.post('/api/cliente/<codigo>')
@auth_decorator
@dbcontext
def create_client(codigo):
    return update_client(codigo)


@api.get('/api/cliente')
@dbcontext
def search_client():
    prefijo = request.query.prefijo
    if prefijo:
        return json_dump(list(clientapi.search(apellido=prefijo)))
    else:
        response.status = 400
        return None


@api.get('/api/nota/<inv_id>')
@dbcontext
@auth_decorator
def get_invoice(inv_id):
    doc = invapi.get_doc(inv_id)
    if doc is None:
        abort(404, 'Nota no encontrado')
        return
    return json_dump(doc.serialize())


@api.post('/api/nota')
@dbcontext
@auth_decorator
def create_invoice():
    json_content = request.body.read()
    content = json_loads(json_content)
    inv = Invoice.deserialize(content)
    inv.items = filter(lambda x: x.cant >= 0, inv.items)
    # convert cant into a decimal. cant is send as int,
    # treating it as a decimal of 3 decimal places
    for item in inv.items:
        item.cant = Decimal(item.cant) / 1000
    inv = invapi.save(inv)

    #increment the next invoice's number
    user = inv.meta.user
    sessionmanager.session.query(NUsuario).filter_by(username=user).update(
        {NUsuario.last_factura: int(inv.meta.codigo) + 1})
    return {'codigo': inv.meta.uid}


@api.put('/api/nota/<uid>')
@auth_decorator
@dbcontext
def postear_invoice(uid):
    t = invapi.commit(uid=uid)
    return {'status': t.meta.status}


@api.delete('/api/nota/<uid>')
@dbcontext
@auth_decorator
def delete_invoice(uid):
    t = invapi.delete(uid=uid)
    return {'status': t.meta.status}


@api.post('/api/pedido')
@dbcontext
@auth_decorator
def save_pedido():
    json_content = request.body.read()
    uid = pedidoapi.save(json_content)
    return {'codigo': uid}


@api.get('/api/pedido/<uid>')
def get_pedido(uid):
    f = pedidoapi.get(uid)
    if f is None:
        response.status = 404
    return f
