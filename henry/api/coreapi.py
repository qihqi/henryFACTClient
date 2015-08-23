from decimal import Decimal
from henry.schema.core import NUsuario
from bottle import Bottle, response, request, abort

from henry.bottlehelper import get_property_or_fail
from henry.base.serialization import SerializableMixin

from henry.config import (prodapi, dbcontext, clientapi, invapi,
                          auth_decorator, pedidoapi, sessionmanager,
                          actionlogged, priceapi)
from henry.base.serialization import json_dumps, json_loads
from henry.schema.core import NNota
from henry.dao import Client, Invoice


api = Bottle()


def mult_thousand(prod):
    if prod.cant_mayorista:
        prod.cant_mayorista *= 1000


# ################ PRICE LIST ############################
@api.get('/api/alm/<almacen_id>/producto')
@dbcontext
@actionlogged
def searchprice(almacen_id):
    prefijo = get_property_or_fail(request.query, 'prefijo')
    print prefijo
    result = list(priceapi.search(**{
        'nombre-prefix': prefijo,
        'almacen_id': almacen_id}))
    use_thousandth = request.query.get('use_thousandth', 1)
    if int(use_thousandth):
        map(mult_thousand, result)
    return json_dumps(result)


@api.get('/api/alm/<almacen_id>/producto/<prod_id:path>')
@dbcontext
@actionlogged
def get_price_by_id(almacen_id, prod_id):
    prod = prodapi.get_producto(prod_id, almacen_id)
    prod = list(priceapi.search(prod_id=prod_id, almacen_id=almacen_id))
    if not prod:
        abort(404)
    obj = prod[0]
    use_thousandth = request.query.get('use_thousandth', '1')
    if int(use_thousandth):
        mult_thousand(obj)
    print obj.serialize()
    return json_dumps(obj.serialize())


# ################ CLIENT ############################
@api.get('/api/cliente/<codigo>')
@dbcontext
@actionlogged
def get_cliente(codigo):
    client = clientapi.get(codigo)
    if client is None:
        abort(404, 'cliente no encontrado')
    return json_dumps(client.serialize())


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
        return json_dumps(list(
            clientapi.search(**{'apellidos-prefix': prefijo})))
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


# ########## NOTA ############################
@api.get('/api/nota/<inv_id>')
@dbcontext
@actionlogged
def get_invoice(inv_id):
    doc = invapi.get_doc(inv_id)
    if doc is None:
        abort(404, 'Nota no encontrado')
        return
    return json_dumps(doc.serialize())


@api.get('/api/alm/<alm_id>/nota/<inv_id>')
@dbcontext
@actionlogged
def get_invoice_from_alm(alm_id, inv_id):
    docdb = sessionmanager.session.query(NNota).filter_by(
        almacen_id=alm_id,
        codigo=inv_id).first()
    if docdb is None:
        abort(404, 'Nota no encontrado')
        return
    doc = invapi.get_doc_from_file(docdb.items_location)
    return json_dumps(doc.serialize())


class InvoiceOptions(SerializableMixin):
    _name = ('crear_cliente', 'revisar_producto',
             'incrementar_codigo', 'usar_decimal', 'no_alm_id')

    def __init__(self):
        self.crear_cliente = False
        self.revisar_producto = False
        self.incrementar_codigo = False
        self.usar_decimal = False
        self.no_alm_id = False


def get_store_by(field, value):
    if field == 'almacen_id':
        return prodapi.get_store_by_id(value)
    canditates = [a for a in prodapi.get_stores() if getattr(a, field) == value]
    if canditates:
        return canditates[0]
    return None


def fix_inv_by_options(inv, options):
    inv.items = filter(lambda x: x.cant >= 0, inv.items)
    inv.meta.paid = True
    for item in inv.items:
        if options.usar_decimal:
            item.cant = Decimal(item.cant)
        else:
            # if not using decimal, means that cant is send as int.
            # treating it as a decimal of 3 decimal places.
            item.cant = Decimal(item.cant) / 1000

        if getattr(item.prod, 'upi', None) is None:
            newprod = prodapi.get_producto(prod_id=item.prod.codigo,
                                           almacen_id=inv.meta.almacen_id)
            item.prod.upi = newprod.upi
            item.prod.multiplicador = newprod.multiplicador

    # Get store: if ruc exists get it takes prescendence. Then name, then id.
    # The reason is that id is mysql autoincrement integer and may not be
    # consistent across different servers
    # using None as default value is buggy. Because there could be store with store.ruc == None
    ruc = getattr(inv.meta, 'almacen_ruc', None)
    name = getattr(inv.meta, 'almacen_name', None)

    alm = None
    if ruc:
        alm = get_store_by('ruc', ruc)
    if name and alm is None:
        alm = get_store_by('nombre', name)
    if alm is None:
        alm = prodapi.get_store_by_id(inv.meta.almacen_id)

    inv.meta.almacen_id = alm.almacen_id
    if options.no_alm_id:
        inv.meta.almacen_id = None
    inv.meta.almacen_name = alm.nombre
    inv.meta.almacen_ruc = alm.ruc
    inv.meta.bodega_id = alm.bodega_id


@api.post('/api/nota')
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
    fix_inv_by_options(inv, options)  # at this point, inv should no longer change
    if options.crear_cliente:  # create client if not exist
        client = inv.meta.client
        if not clientapi.get(client.codigo):
            clientapi.save(client)

    if options.revisar_producto:  # make sure all product exists
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
        sessionmanager.session.commit()
    return {'codigo': inv.meta.uid}


@api.put('/api/nota/<uid>')
@dbcontext
@auth_decorator
@actionlogged
def postear_invoice(uid):
    inv = invapi.get_doc(uid)
    invapi.commit(inv)
    return {'status': inv.meta.status}


@api.delete('/api/nota/<uid>')
@dbcontext
@auth_decorator
@actionlogged
def delete_invoice(uid):
    inv = invapi.get_doc(uid)
    invapi.delete(inv)
    return {'status': inv.meta.status}

from henry.authentication import app
api.merge(app)
