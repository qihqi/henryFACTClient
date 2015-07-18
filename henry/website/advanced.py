from collections import defaultdict
import datetime
from bottle import Bottle, request, abort
from henry.base.schema import NProducto, NContenido, NBodega, NCategory
from henry.config import dbcontext, auth_decorator, prodapi, jinja_env, sessionmanager, invapi, transactionapi
from henry.dao import Item
from henry.website.common import parse_start_end_date

webadv = w = Bottle()


@w.get('/app/adv')
@auth_decorator
def index():
    return '''
    <a href="/app/pricelist">Price List</a>
    <a href="/app/vendidos_por_categoria">Por Categoria</a>
    <a href="/app/ver_transacciones">Transacciones</a>
    <a href="/app/ver_ventas">Ventas</a>
    '''


@w.get('/app/pricelist')
@dbcontext
@auth_decorator
def get_price_list():
    almacen_id = request.query.get('almacen_id')
    prefix = request.query.get('prefix')
    if not prefix:
        prefix = ''
    if almacen_id is None:
        abort(400, 'input almacen_id')
    prods = prodapi.search_producto(prefix=prefix, almacen_id=almacen_id)
    temp = jinja_env.get_template('buscar_precios.html')
    return temp.render(prods=prods)


@w.get('/app/vendidos_por_categoria_form')
@dbcontext
@auth_decorator
def vendidos_por_categoria_form():
    temp = jinja_env.get_template('vendidos_por_categoria_form.html')
    categorias = sessionmanager.session.query(NCategory)
    return temp.render(cat=categorias)


def full_invoice_items(api, start_date, end_date):
    invs = api.search_metadata_by_date_range(start_date, end_date)
    for inv in invs:
        fullinv = invapi.get_doc_from_file(inv.items_location)
        if fullinv is None:
            continue
        for x in fullinv.items:
            yield inv, x


@w.get('/app/vendidos_por_categoria')
@dbcontext
@auth_decorator
def vendidos_por_categoria():
    cat = request.query.categoria_id
    start, end = parse_start_end_date(request.query)
    prods = sessionmanager.session.query(NProducto.codigo).filter_by(
        categoria_id=cat)
    all_codigos = {p.codigo for p in prods}

    all_items = []
    total = 0
    for inv, x in full_invoice_items(invapi, start, end):
        if x.prod.codigo in all_codigos:
            x.prod.precio = (x.prod.precio1 if x.cant >= x.prod.threshold
                             else x.prod.precio2)
            x.subtotal = x.prod.precio * x.cant
            total += x.subtotal
            all_items.append((inv, x))

    temp = jinja_env.get_template('ver_vendidos.html')
    return temp.render(items=all_items, total=total)


@w.get('/app/ver_transacciones')
@dbcontext
@auth_decorator
def ver_transacciones():
    prod_id = request.query.prod_id
    bodega_id = request.query.bodega_id
    start, end = parse_start_end_date(request.query)
    if end is None:
        end = datetime.date.today()
    if start is None:
        start = datetime.date.today() - datetime.timedelta(days=7)
    items = sorted(transactionapi.get_transactions(prod_id, start, end),
                   key=lambda i: i.fecha, reverse=True)
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


@w.get('/app/ver_ventas')
@dbcontext
@auth_decorator
def sale_by_product():
    start, end = parse_start_end_date(request.query)
    alm_id = int(request.query.get('almacen_id', 1))
    almacen = prodapi.get_store_by_id(alm_id)
    if not end:
        end = datetime.datetime.now()
    if not start:
        start = end - datetime.timedelta(days=7)
    prods_sale = defaultdict(Item)
    for inv, x in full_invoice_items(invapi, start, end):
        if inv.almacen_id != almacen.almacen_id:
            continue
        obj = prods_sale[x.prod.codigo]
        obj.prod = x.prod
        if obj.cant:
            obj.cant += x.cant
        else:
            obj.cant = x.cant
    temp = jinja_env.get_template('ver_ventas_por_prod.html')
    values = sorted(prods_sale, key=lambda x: x.cant * x.prod.precio1)
    return temp.render(items=values, start=start, end=end, almacen=almacen.nombre,
                       almacenes=prodapi.get_stores())
