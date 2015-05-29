import sys
import datetime
import json
from decimal import Decimal

from bottle import Bottle, response, request, abort

from henry.layer1.schema import NUsuario
from henry.config import (prodapi, transapi, dbcontext, clientapi,
                          invapi, auth_decorator, pedidoapi, sessionmanager)
from henry.helpers.serialization import json_dump, json_loads
from henry.dao import Client, Invoice, Transferencia
from henry.authentication import get_session
from henry.helpers.connection import timed

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
@dbcontext
@auth_decorator
def crear_ingreso():
    json_content = request.body.read()
    content = json_loads(json_content)
    ingreso = Transferencia.deserialize(content)
    codigo = transapi.create(ingreso)
    return {'codigo': codigo}


@api.put('/api/ingreso/<ingreso_id>')
@dbcontext
@auth_decorator
def postear_ingreso(ingreso_id):
    trans = transapi.get_doc(ingreso_id)
    transapi.commit(trans)
    return {'status': trans.meta.status}


@api.delete('/api/ingreso/<ingreso_id>')
@dbcontext
def delete_ingreso(ingreso_id):
    trans = transapi.get_doc(ingreso_id)
    transapi.delete(trans)
    return {'status': trans.meta.status}


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
@dbcontext
@auth_decorator
def update_client(codigo):
    client_dict = json.parse(request.body)
    client = Client.deserialize(client_dict)
    clientapi.save(client)
    return {'codigo': client.codigo}


@api.post('/api/cliente/<codigo>')
@dbcontext
@auth_decorator
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


@api.get('/api/nota')
@dbcontext
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
    return json_dump(list(result))


@api.post('/api/nota')
@dbcontext
@auth_decorator
def create_invoice():
    json_content = request.body.read() 
    if not json_content:
        return ''
    content = json_loads(json_content)
    inv = Invoice.deserialize(content)
    inv.items = filter(lambda x: x.cant >= 0, inv.items)
    inv.meta.bodega_id = prodapi.get_store_by_id(inv.meta.almacen_id).bodega_id
    inv.meta.paid = True
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
@dbcontext
@auth_decorator
def postear_invoice(uid):
    inv = invapi.get_doc(uid)
    invapi.commit(inv)
    return {'status': inv.meta.status}


@api.delete('/api/nota/<uid>')
@dbcontext
@auth_decorator
def delete_invoice(uid):
    inv = invapi.get_doc(uid)
    invapi.delete(inv)
    return {'status': inv.meta.status}


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
