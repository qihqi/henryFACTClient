import datetime
from decimal import Decimal
from bottle import Bottle, request, abort

from henry.base.serialization import json_dumps, json_loads, SerializableMixin
from henry.base.schema import NUsuario, NInventoryRevision, NInventoryRevisionItem
from henry.config import (transapi, dbcontext, prodapi, clientapi,
                          invapi, auth_decorator, sessionmanager,
                          actionlogged, transactionapi)
from henry.dao import Invoice, Transferencia, Transaction

napi = Bottle()


# ########## NOTA ############################
@napi.get('/api/nota/<inv_id>')
@dbcontext
@actionlogged
def get_invoice(inv_id):
    doc = invapi.get_doc(inv_id)
    if doc is None:
        abort(404, 'Nota no encontrado')
        return
    return json_dumps(doc.serialize())


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
    return json_dumps(list(result))


class InvoiceOptions(SerializableMixin):
    _name = ('crear_cliente', 'revisar_producto',
             'incrementar_codigo', 'usar_decimal')

    def __init__(self):
        self.crear_cliente = False
        self.revisar_producto = False
        self.incrementar_codigo = False
        self.usar_decimal = False


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
    inv.meta.almacen_name = alm.nombre
    inv.meta.almacen_ruc = alm.ruc
    inv.meta.bodega_id = alm.bodega_id


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
    return json_dumps(ing.serialize())


@napi.put('/api/revision/<rid>')
@dbcontext
@auth_decorator
@actionlogged
def put_revision(rid):
    revision = sessionmanager.session.query(NInventoryRevision, NInventoryRevisionItem).filter(
        NInventoryRevision.uid == NInventoryRevisionItem.revision_id).filter(
        NInventoryRevision.uid == rid)
    reason = 'Revision: codigo {}'.format(rid)
    now = datetime.datetime.now()
    for rev, item in revision:
        bodega_id = rev.bodega_id
        delta = item.real_cant - item.inv_cant
        transaction = Transaction(
            upi=None,
            bodega_id=bodega_id,
            prod_id=item.prod_id,
            delta=delta,
            ref=reason,
            fecha=now)
        transactionapi.save(transaction)
    return {'status': 'AJUSTADO'}
