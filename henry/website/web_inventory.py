import datetime
from decimal import Decimal
from operator import attrgetter
import traceback

from sqlalchemy.exc import IntegrityError

from bottle import request, Bottle, abort, redirect, response

from henry.config import jinja_env, transapi, prodapi, invapi, actionlogged
from henry.config import (dbcontext, auth_decorator, sessionmanager, clientapi,
                          BODEGAS_EXTERNAS, transactionapi, pedidoapi)
from henry.dao import Item, TransType, TransMetadata, Transferencia, Product, Status, InvMetadata, Client, Invoice, PaymentFormat
from henry.dao.productos import Bodega
from henry.base.schema import NUsuario, NNota, NCliente, NProducto, NAccountStat, NCategory, NContenido, NBodega
from henry.dao.exceptions import ItemAlreadyExists
from henry.base.serialization import json_loads
from henry.reports import get_notas_with_clients, split_records, group_by_records
from henry.base.auth import get_user

w = Bottle()
web_inventory_webapp = w

datestrp = datetime.datetime.strptime


@w.get('/app')
@dbcontext
@auth_decorator
def index():
    return jinja_env.get_template('base.html').render()


@w.get('/app/ingreso/<uid>')
@dbcontext
@auth_decorator
def get_ingreso(uid):
    trans = transapi.get_doc(uid)
    if trans:
        temp = jinja_env.get_template('ingreso.html')
        if trans.meta.origin is not None:
            trans.meta.origin = prodapi.get_bodega_by_id(trans.meta.origin).nombre
        if trans.meta.dest is not None:
            trans.meta.dest = prodapi.get_bodega_by_id(trans.meta.dest).nombre
        return temp.render(ingreso=trans)
    return 'Documento con codigo {} no existe'.format(uid)


@w.get('/app/nota/<uid>')
@dbcontext
@auth_decorator
def get_nota(uid):
    doc = invapi.get_doc(uid)
    if doc:
        temp = jinja_env.get_template('nota.html')
        return temp.render(inv=doc)
    return 'Documento con codigo {} no existe'.format(uid)


@w.get('/app/crear_ingreso')
@dbcontext
@auth_decorator
def crear_ingreso():
    temp = jinja_env.get_template('crear_ingreso.html')
    bodegas = prodapi.get_bodegas()
    bodegas_externas = [Bodega(id=i, nombre=n[0]) for i, n in enumerate(BODEGAS_EXTERNAS)]
    return temp.render(bodegas=bodegas, externas=bodegas_externas,
                       types=TransType.names)

@w.get('/app/ver_ingreso_form')
@dbcontext
@auth_decorator
def ver_ingreso_form():
    return jinja_env.get_template('ver_ingreso_form.html').render()


def items_from_form(form):
    items = []
    for cant, prod_id in zip(
            form.getlist('cant'),
            form.getlist('codigo')):
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
    return items


def transmetadata_from_form(form):
    meta = TransMetadata()
    meta.dest = form.get('dest')
    meta.origin = form.get('origin')
    try:
        meta.dest = int(meta.dest)
        meta.origin = int(meta.origin)
    except ValueError:
        pass
    meta.meta_type = form.get('meta_type')
    meta.trans_type = form.get('trans_type')
    if meta.trans_type == TransType.INGRESS:
        meta.origin = None  # ingress does not have origin
    if meta.trans_type in (TransType.EXTERNAL or TransType.EGRESS):
        meta.dest = None  # dest for external resides in other server
    if meta.timestamp is None:
        meta.timestamp = datetime.datetime.now()
    return meta


@w.post('/app/crear_ingreso')
@dbcontext
@auth_decorator
@actionlogged
def post_crear_ingreso():
    meta = transmetadata_from_form(request.forms)
    items = items_from_form(request.forms)
    try:
        transferencia = Transferencia(meta, items)
        if meta.trans_type == TransType.EXTERNAL:
            newmeta = TransMetadata().merge_from(meta)
            external_bodega_index = int(request.forms['externa'])
            _, api, dest_id = BODEGAS_EXTERNAS[external_bodega_index]
            newmeta.dest = dest_id
            newmeta.origin = None
            newmeta.trans_type = TransType.INGRESS
            t = api.save(Transferencia(newmeta, items))
            if t is None:
                abort(400)
            transferencia.meta.ref = t.meta.ref
        transferencia = transapi.save(transferencia)
        redirect('/app/ingreso/{}'.format(transferencia.meta.uid))
    except ValueError as e:
        traceback.print_exc()
        abort(400, str(e))


@w.get('/app/crear_producto')
@dbcontext
@auth_decorator
def create_prod_form(message=''):
    temp = jinja_env.get_template('crear_producto.html')
    stores = prodapi.get_stores()
    categorias = prodapi.get_category()
    return temp.render(almacenes=stores, categorias=categorias, message=message)


def convert_to_cent(dec):
    if not isinstance(dec, Decimal):
        dec = Decimal(dec)
    return int(dec * 100)


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
        if p1 and p2:
            p1 = convert_to_cent(p1)
            p2 = convert_to_cent(p2)
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
        abort(400, 'Hay que ingresar las fechas')

    start = datestrp(start, '%Y-%m-%d')
    end = datestrp(end, '%Y-%m-%d')
    store = int(store)

    session = sessionmanager.session
    result = get_notas_with_clients(session, store, start, end)

    by_status = split_records(result, lambda x: x.status)
    deleted = by_status[Status.DELETED]
    committed = by_status[Status.COMITTED]
    ventas = split_records(committed, lambda x: x.payment_format)

    gtotal = sum((x.total for x in committed))
    temp = jinja_env.get_template('resumen.html')
    return temp.render(
        start=start,
        end=end,
        user=user,
        store=prodapi.get_store_by_id(store),
        ventas=ventas,
        gtotal=gtotal,
        eliminados=deleted)


@w.get('/app/eliminar_factura')
@dbcontext
@auth_decorator
def eliminar_factura_form(message=None):
    almacenes = list(prodapi.get_stores())
    print almacenes
    temp = jinja_env.get_template('eliminar_factura.html')
    return temp.render(almacenes=almacenes, message=message)


@w.post('/app/eliminar_factura')
@dbcontext
@auth_decorator
@actionlogged
def eliminar_factura():
    almacen = int(request.forms.get('almacen'))
    codigo = request.forms.get('codigo').strip()
    # ref = request.forms.get('ref')  # TODO: have to save this
    print almacen, codigo
    db_instance = sessionmanager.session.query(
        NNota.id, NNota.status, NNota.items_location).filter_by(
        almacen_id=almacen, codigo=codigo).first()
    if db_instance is None:
        return eliminar_factura_form('Factura no existe')
    doc = invapi.get_doc_from_file(db_instance.items_location)
    doc.meta.status = db_instance.status

    try:
        invapi.delete(doc)
    except ValueError:
        abort(400)

    redirect('/app/nota/{}'.format(db_instance.id))


@w.get('/app/ver_factura_form')
@dbcontext
@auth_decorator
def get_nota_form(message=None):
    almacenes = list(prodapi.get_stores())
    temp = jinja_env.get_template('ver_factura_form.html')
    return temp.render(almacenes=almacenes, message=message)


@w.get('/app/ver_factura')
@dbcontext
@auth_decorator
def ver_factura():
    almacen = int(request.query.get('almacen'))
    codigo = request.query.get('codigo').strip()
    print almacen, codigo
    db_instance = sessionmanager.session.query(
        NNota.id, NNota.status, NNota.items_location).filter_by(
        almacen_id=almacen, codigo=codigo).first()
    if db_instance is None:
        return get_nota_form('Factura no existe')
    redirect('/app/nota/{}'.format(db_instance.id))


@w.get('/app/ver_producto_form')
@auth_decorator
def ver_producto_form():
    return jinja_env.get_template('ver_item.html').render(
        title='Ver Producto',
        baseurl='/app/producto',
        apiurl='/api/producto')


@w.get('/app/producto/<uid>')
@dbcontext
@auth_decorator
def ver_producto(uid):
    prod = prodapi.get_producto_full(uid)
    price_dict = {}
    for x in prod.precios:
        price_dict[x.almacen_id] = x
    prod.precios = price_dict
    temp = jinja_env.get_template('producto.html')
    return temp.render(prod=prod, stores=prodapi.get_stores())


@w.get('/app/producto')
@dbcontext
@auth_decorator
def buscar_producto_result():
    prefix = request.query.prefijo
    if prefix is None:
        redirect('/app/ver_producto_form')
    prods = prodapi.search_producto(prefix)
    temp = jinja_env.get_template('buscar_producto_result.html')
    return temp.render(prods=prods)


@w.get('/app/crear_cliente')
@dbcontext
@auth_decorator
def crear_cliente_form(message=None):
    temp = jinja_env.get_template('crear_cliente.html')
    return temp.render(client=None, message=message, action='/app/crear_cliente',
                       button_text='Crear')


@w.get('/app/cliente/<id>')
@dbcontext
@auth_decorator
def modificar_cliente_form(id, message=None):
    client = clientapi.get(id)
    if client is None:
        message = 'Cliente {} no encontrado'.format(id)
    temp = jinja_env.get_template('crear_cliente.html')
    return temp.render(client=client, message=message, action='/app/modificar_cliente',
                       button_text='Modificar')


@w.get('/app/cliente')
@dbcontext
@auth_decorator
def search_cliente_result():
    prefix = request.query.prefijo
    clientes = list(clientapi.search(prefix))
    temp = jinja_env.get_template('search_cliente_result.html')
    return temp.render(clientes=clientes)


@w.get('/app/ver_cliente')
@dbcontext
@auth_decorator
def ver_cliente():
    temp = jinja_env.get_template('ver_item.html')
    return temp.render(title='Ver Cliente', baseurl='/app/cliente',
                       apiurl='/api/cliente')


@w.post('/app/crear_cliente')
@dbcontext
@auth_decorator
def crear_cliente():
    cliente = Client.deserialize(request.forms)
    try:
        clientapi.create(cliente)
    except ItemAlreadyExists:
        return crear_cliente_form('Cliente con codigo {} ya existe'.format(cliente.codigo))
    return crear_cliente_form('Cliente {} {} creado'.format(cliente.apellidos, cliente.nombres))


@w.get('/app/secuencia')
@dbcontext
@auth_decorator
def get_secuencia():
    users = list(sessionmanager.session.query(NUsuario))
    temp = jinja_env.get_template('secuencia.html')
    store_dict = {s.almacen_id: s.nombre for s in prodapi.get_stores()}
    store_dict[-1] = 'Ninguno'
    return temp.render(users=users, stores=store_dict)


@w.post('/app/secuencia')
@dbcontext
@auth_decorator
@actionlogged
def post_secuencia():
    username = request.forms.usuario
    seq = request.forms.secuencia
    alm = request.forms.almacen_id
    sessionmanager.session.query(NUsuario).filter_by(
        username=username).update({'last_factura': seq, 'bodega_factura_id': alm})
    redirect('/app/secuencia')


@w.get('/app/nota_de_pedido')
@dbcontext
@auth_decorator
def get_notas_de_pedido_form():
    session = request.environ.get('beaker.session')
    if session is None or 'login_info' not in session:
        response.status = 401
        response.set_header('www-authenticate', 'Basic realm="Henry"')
        return ''
    temp = jinja_env.get_template('crear_pedido.html')
    return temp.render()


@w.get('/app/pedido/<uid>')
@dbcontext
@auth_decorator
def get_notas_de_pedido(uid):
    pedido = pedidoapi.get_doc(uid)
    pedido = Invoice.deserialize(json_loads(pedido))
    pedido.meta.uid = uid
    for i in pedido.items:
        i.cant = Decimal(i.cant) / 1000
    willprint = request.query.get('print')
    temp = jinja_env.get_template('ver_pedido.html')
    return temp.render(pedido=pedido, willprint=willprint)

@w.get('/app/vendidos_por_categoria_form')
@dbcontext
@auth_decorator
def vendidos_por_categoria_form():
    temp = jinja_env.get_template('vendidos_por_categoria_form.html')
    categorias = sessionmanager.session.query(NCategory)
    return temp.render(cat=categorias)


@w.get('/app/vendidos_por_categoria')
@dbcontext
@auth_decorator
def vendidos_por_categoria():
    cat = request.query.categoria_id
    start = datestrp(request.query.start_date, '%Y-%m-%d')
    end = datestrp(request.query.end_date, '%Y-%m-%d')
    prods = sessionmanager.session.query(NProducto.codigo).filter_by(
        categoria_id=cat)
    all_codigos = {p.codigo for p in prods}

    all_items = []
    invs = invapi.search_metadata_by_date_range(start, end)
    total = 0
    for inv in invs:
        fullinv = invapi.get_doc_from_file(inv.items_location)
        if fullinv is None:
            print 'fullinv is None'
            continue
        for x in fullinv.items:
            if x.prod.codigo in all_codigos:
                x.prod.precio = (x.prod.precio1 if x.cant >= x.prod.threshold
                                 else x.prod.precio2)
                x.subtotal = x.prod.precio * x.cant
                total += x.subtotal
                all_items.append((inv, x))

    temp = jinja_env.get_template('ver_vendidos.html')
    return temp.render(items=all_items, total=total)


@w.get('/app/entregar_cuenta_form')
@dbcontext
@auth_decorator
def entrega_de_cuenta():
    temp = jinja_env.get_template('entregar_cuenta_form.html')
    return temp.render()


@w.get('/app/crear_entrega_de_cuenta')
@dbcontext
@auth_decorator
def crear_entrega_de_cuenta():
    date = request.query.get('fecha')
    date = datetime.datetime.strptime(date, '%Y-%m-%d')

    all_sale = list(get_notas_with_clients(sessionmanager.session, None, date, date))

    by_status = split_records(all_sale, attrgetter('status'))
    deleted = by_status[Status.DELETED]
    committed = by_status[Status.COMITTED]

    by_payment = split_records(committed, attrgetter('payment_format'))
    cashed = by_payment[PaymentFormat.CASH]
    sale_by_store = group_by_records(cashed, attrgetter('almacen_name'), attrgetter('total'))
    total_cash = sum(sale_by_store.values())

    otros_pagos = by_payment
    del otros_pagos[PaymentFormat.CASH]

    existing = sessionmanager.session.query(NAccountStat).filter_by(date=date).first()
    temp = jinja_env.get_template('crear_entregar_cuenta_form.html')
    return temp.render(
        cash=sale_by_store, others=otros_pagos,
        total_cash=total_cash,
        deleted=deleted,
        date=date.date().isoformat(),
        existing=existing)


@w.post('/app/crear_entrega_de_cuenta')
@dbcontext
@auth_decorator
def post_crear_entrega_de_cuenta():
    cash = request.forms.get('cash')
    gastos = request.forms.get('gastos')
    deposito = request.forms.get('deposito')
    turned_cash = request.forms.get('valor')
    date = request.forms.get('date')

    cash = int(float(cash) * 100)
    gastos = int(float(gastos) * 100)
    deposito = int(float(deposito) * 100)
    turned_cash = int(float(turned_cash) * 100)
    date = datetime.datetime.strptime(date, '%Y-%m-%d').date()

    userid = get_user(request)['username']
    if request.forms.get('submit') == 'Crear':
        stat = NAccountStat(
            date=date,
            total_spend=gastos,
            turned_cash=turned_cash,
            deposit=deposito,
            diff=(cash - gastos - deposito - turned_cash),
            created_by=userid
            )
        sessionmanager.session.add(stat)
        sessionmanager.session.flush()
    else:
        sessionmanager.session.query(NAccountStat).filter_by(date=date).update(
                {'revised_by': userid})
    redirect('/app/crear_entrega_de_cuenta?fecha={}'.format(date.isoformat()))


@w.get('/app/entrega_de_cuenta_list')
@dbcontext
@auth_decorator
def ver_entrega_de_cuenta_list():
    end = datetime.date.today()
    start = datetime.date.today() - datetime.timedelta(days=7)
    if request.query.get('start', None):
        start = datestrp(request.query.start, '%Y-%m-%d').date()
    if request.query.get('end', None):
        end = datestrp(request.query.end, '%Y-%m-%d').date()

    accts = sessionmanager.session.query(NAccountStat).filter(
        NAccountStat.date >= start, NAccountStat.date <= end)
    temp = jinja_env.get_template('entrega_de_cuenta_list.html')
    return temp.render(accts=accts, start=start, end=end)


@w.get('/app/ver_transacciones')
@dbcontext
@auth_decorator
def ver_transacciones():
    prod_id = request.query.prod_id
    end = datetime.date.today()
    start = datetime.date.today() - datetime.timedelta(days=7)
    bodega_id = request.query.bodega_id
    if request.query.get('start', None):
        start = datestrp(request.query.start, '%Y-%m-%d').date()
    if request.query.get('end', None):
        end = datestrp(request.query.end, '%Y-%m-%d').date()
    items = sorted(transactionapi.get_transactions(prod_id, start, end),
                   key=lambda x: x.fecha, reverse=True)
    counts = {}
    count_expr = sessionmanager.session.query(NContenido).filter_by(prod_id=prod_id)
    if bodega_id is not None:
        bodega_id = int(bodega_id)
        if bodega_id == -1:
            bodega_id = None

    for x in count_expr:
        counts[x.bodega_id] = x.cant
    if bodega_id:
        items = filter(lambda i: i.bodega_id == bodega_id, items)
    for i in items:
        i.bodega_name = prodapi.get_bodega_by_id(i.bodega_id).nombre
        i.count = counts[i.bodega_id]
        counts[i.bodega_id] += i.delta

    bodegas = prodapi.get_bodegas()
    bodegas.append(NBodega(id=-1, nombre='Todas'))
    temp = jinja_env.get_template('ver_transacciones.html')
    return temp.render(items=items, start=start, end=end,
                       prod_id=prod_id, bodegas=bodegas, bodega_id=bodega_id)


from .advanced import w as aw
w.merge(aw)

