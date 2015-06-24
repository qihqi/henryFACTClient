import datetime
from decimal import Decimal
from bottle import Bottle, request, abort

from henry.base.serialization import json_dump, json_loads, SerializableMixin
from henry.base.schema import NUsuario
from henry.config import (transapi, dbcontext, prodapi, clientapi,
                          invapi, auth_decorator, sessionmanager,
                          actionlogged)
from henry.dao import Invoice, Transferencia


napi = Bottle()

# ########## NOTA ############################
@napi.get('/api/nota/<inv_id>')
@dbcontext
@auth_decorator
@actionlogged
def get_invoice(inv_id):
    doc = invapi.get_doc(inv_id)
    if doc is None:
        abort(404, 'Nota no encontrado')
        return
    return json_dump(doc.serialize())


@napi.get('/api/nota')
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
    return json_dump(list(result))


class InvoiceOptions(SerializableMixin):
    _name = ('crear_cliente', 'revisar_producto', 'incrementar_codigo')

    def __init__(self):
        self.crear_cliente = False
        self.revisar_producto = False
        self.incrementar_codigo = False


@napi.post('/api/nota')
@dbcontext
@auth_decorator
@actionlogged
def create_invoice():
    json_content = request.body.read()
    if not json_content:
        return ''
    content = json_loads(json_content)
    options = InvoiceOptions()
    if 'options' in content:
        op = content['options']
        options.merge_from(op)
        del content['options']

    inv = Invoice.deserialize(content)
    inv.items = filter(lambda x: x.cant >= 0, inv.items)
    inv.meta.bodega_id = prodapi.get_store_by_id(inv.meta.almacen_id).bodega_id
    inv.meta.paid = True
    # convert cant into a decimal. cant is send as int,
    # treating it as a decimal of 3 decimal places
    for item in inv.items:
        item.cant = Decimal(item.cant) / 1000

    if options.crear_cliente:
        client = inv.meta.client
        if not clientapi.get(client.codigo):
            clientapi.save(client)

    if options.revisar_producto:
        for item in inv.items:
            prod_id = item.prod.codigo
            if not prodapi.get_producto(prod_id):
                abort(400, 'Producto con codigo {} no existe'.format(prod_id))

    inv = invapi.save(inv)

    # increment the next invoice's number
    if options.incrementar_codigo:
        user = inv.meta.user
        sessionmanager.session.query(NUsuario).filter_by(username=user).update(
            {NUsuario.last_factura: int(inv.meta.codigo) + 1})
    return {'codigo': inv.meta.uid}


@napi.put('/api/nota/<uid>')
@dbcontext
@auth_decorator
@actionlogged
def postear_invoice(uid):
    inv = invapi.get_doc(uid)
    invapi.commit(inv)
    return {'status': inv.meta.status}


@napi.delete('/api/nota/<uid>')
@dbcontext
@auth_decorator
@actionlogged
def delete_invoice(uid):
    inv = invapi.get_doc(uid)
    invapi.delete(inv)
    return {'status': inv.meta.status}


# ################# INGRESO ###########################3
@napi.post('/api/ingreso')
@dbcontext
@auth_decorator
@actionlogged
def crear_ingreso():
    json_content = request.body.read()
    json_dict = json_loads(json_content)
    ingreso = Transferencia.deserialize(json_dict)
    ingreso = transapi.save(ingreso)
    return {'codigo': ingreso.meta.uid}


@napi.put('/api/ingreso/<ingreso_id>')
@dbcontext
@auth_decorator
@actionlogged
def postear_ingreso(ingreso_id):
    trans = transapi.get_doc(ingreso_id)
    transapi.commit(trans)
    return {'status': trans.meta.status}


@napi.delete('/api/ingreso/<ingreso_id>')
@dbcontext
@actionlogged
def delete_ingreso(ingreso_id):
    trans = transapi.get_doc(ingreso_id)
    transapi.delete(trans)
    return {'status': trans.meta.status}


@napi.get('/api/ingreso/<ingreso_id>')
@dbcontext
@actionlogged
def get_ingreso(ingreso_id):
    ing = transapi.get_doc(ingreso_id)
    if ing is None:
        abort(404, 'Ingreso No encontrada')
        return
    return json_dump(ing.serialize())
