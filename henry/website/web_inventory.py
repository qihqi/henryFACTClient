import datetime
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from bottle import request, Bottle, abort, redirect
from henry.config import jinja_env, transapi, prodapi, invapi
from henry.config import dbcontext, auth_decorator, sessionmanager
from henry.dao import Item, TransType, TransMetadata, Transferencia, Product, Status, InvMetadata
from henry.layer1.schema import NUsuario, NNota, NCliente

w = Bottle()
web_inventory_webapp = w


@w.get('/app/ingreso/<uid>')
@dbcontext
@auth_decorator
def get_ingreso(uid):
    trans = transapi.get_doc(uid)
    bodegas = {x.id: x.nombre for x in prodapi.get_bodegas()}
    if trans:
        print trans.serialize()
        temp = jinja_env.get_template('ingreso.html')
        return temp.render(ingreso=trans, bodega_mapping=bodegas)
    else:
        return 'Documento con codigo {} no existe'.format(uid)


@w.get('/app/crear_ingreso')
@dbcontext
@auth_decorator
def crear_ingreso():
    temp = jinja_env.get_template('crear_ingreso.html')
    bodegas = prodapi.get_bodegas()
    return temp.render(bodegas=bodegas, types=TransType.names)


@w.post('/app/crear_ingreso')
@dbcontext
@auth_decorator
def post_crear_ingreso():
    meta = TransMetadata()
    items = []
    meta.dest = int(request.forms.get('dest'))
    meta.origin = int(request.forms.get('origin'))
    meta.meta_type = request.forms.get('meta_type')
    meta.trans_type = request.forms.get('trans_type')
    if meta.trans_type == TransType.INGRESS:
        meta.origin = None  # ingress does not have origin
    meta.timestamp = datetime.datetime.now()
    for cant, prod_id in zip(
            request.forms.getlist('cant'),
            request.forms.getlist('codigo')):
        if not cant.strip() or not prod_id.strip():
            # skip empty lines
            continue
        try:
            cant = Decimal(cant)
        except ValueError:
            abort(400, 'cantidad debe ser entero positivo')
        if cant < 0:
            abort(400, 'cantidad debe ser entero positivo')
        items.append(Item(prodapi.get_producto(prod_id), cant))
    try:
        transferencia = Transferencia(meta, items)
        transferencia = transapi.save(transferencia)
    except ValueError as e:
        abort(400, str(e))

    redirect('/app/ingreso/{}'.format(transferencia.meta.uid))


@w.get('/app/crear_producto')
@dbcontext
@auth_decorator
def create_prod_form(message=''):
    temp = jinja_env.get_template('crear_producto.html')
    stores = prodapi.get_stores()
    categorias = prodapi.get_category()
    return temp.render(almacenes=stores, categorias=categorias, message=message)


@w.post('/app/crear_producto')
@dbcontext
@auth_decorator
def create_prod():
    p = Product()
    p.codigo = request.forms.codigo
    p.nombre = request.forms.nombre
    p.categoria = request.forms.categoria

    precios = {}
    for alm in prodapi.get_stores():
        p1 = request.forms.get('{}-precio1'.format(alm.almacen_id))
        p2 = request.forms.get('{}-precio2'.format(alm.almacen_id))
        thres = request.forms.get('{}-thres'.format(alm.almacen_id))
        precios[alm.almacen_id] = (p1, p2, thres)

    try:
        prodapi.create_product(p, precios)
        message = 'producto con codigo "{}" creado'.format(p.codigo)
    except IntegrityError:
        message = 'Producto con codigo {} ya existe'.format(p.codigo)

    return create_prod_form(message=message)


@w.get('/app/resumen_form')
@dbcontext
@auth_decorator
def resume_form():
    temp = jinja_env.get_template('resumen_form.html')
    stores = prodapi.get_stores()
    users = list(sessionmanager.session.query(NUsuario))
    return temp.render(almacenes=stores, users=users)


@w.get('/app/resumen')
@dbcontext
@auth_decorator
def get_resumen():
    start = request.query.get('start_date')
    end = request.query.get('end_date')
    user = request.query.get('user')
    store = request.query.get('almacen')

    if start is None or end is None:
        pass

    datestrp = datetime.datetime.strptime
    start = datestrp(start, '%Y-%m-%d')
    end = datestrp(end, '%Y-%m-%d')
    store = int(store)

    session = sessionmanager.session
    def decode_db_row_with_client(db_raw):
        m = InvMetadata.from_db_instance(db_raw[0])
        m.client.nombres = db_raw.nombres
        m.client.apellidos = db_raw.apellidos
        return m
        
    result = session.query(NNota, NCliente.nombres, NCliente.apellidos).filter_by(
        user_id=user,
        almacen_id=store).filter(
        NNota.timestamp >= start).filter(
        NNota.timestamp <= end).filter(NCliente.codigo == NNota.client_id)
    result = map(decode_db_row_with_client, result)
    deleted = [x for x in result if x.status == Status.DELETED]
    committed = [x for x in result if x.status != Status.DELETED]
    def pago(value):
        return lambda x: x.payment_format == value
    efectivos = filter(pago('efectivo'), committed)
    creditos = filter(pago('credito'), committed)
    cheques = filter(pago('cheque'), committed)
    depositos = filter(pago('deposito'), committed)
    gtotal = sum((x.total for x in committed))

    temp = jinja_env.get_template('resumen.html')
    return temp.render(
        start=start,
        end=end,
        user=user,
        store=prodapi.get_store_by_id(store),
        efectivos=efectivos,
        creditos=creditos,
        cheques=cheques,
        depositos=depositos,
        gtotal=gtotal,
        eliminados=deleted)
