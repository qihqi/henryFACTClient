import datetime
from bottle import Bottle, request, abort
from henry.base.schema import NProducto, NContenido, NBodega
from henry.config import dbcontext, auth_decorator, prodapi, jinja_env, sessionmanager, invapi, transactionapi
from henry.website.common import parse_start_end_date

webadv = w = Bottle()


@w.get('/app/adv')
@auth_decorator
def index():
    return '''
    <a href="/app/pricelist">Price List</a>
    <a href="/app/vendidos_por_categoria">Por Categoria</a>
    <a href="/app/ver_transacciones">Transacciones</a>
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