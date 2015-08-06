from collections import defaultdict
import datetime
from bottle import Bottle, request, abort, redirect
from sqlalchemy import desc

from henry.base.auth import get_user
from henry.base.schema import (NProducto, NContenido, NBodega, NCategory,
                               NPriceList, NNota, NComment, ObjType)
from henry.config import (dbcontext, auth_decorator, prodapi, jinja_env,
                          sessionmanager, invapi, transactionapi,
                          actionlogged)
from henry.dao import Item, PaymentFormat
from henry.website.common import parse_start_end_date_with_default, parse_start_end_date

webadv = w = Bottle()


@w.get('/app/adv')
@auth_decorator
def index():
    return '''
    <a href="/app/pricelist">Price List</a>
    <a href="/app/vendidos_por_categoria_form">Por Categoria</a>
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
    prod_id = request.query.prod_id or '123'
    bodega_id = request.query.bodega_id or 1
    today = datetime.date.today()
    start, end = parse_start_end_date_with_default(
        request.query, today - datetime.timedelta(days=7), today)
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
    print items
    for i in items:
        i.bodega_name = prodapi.get_bodega_by_id(i.bodega_id).nombre
        i.count = counts[i.bodega_id]
        counts[i.bodega_id] -= i.delta
    print items
    bodegas = prodapi.get_bodegas()
    bodegas.append(NBodega(id=-1, nombre='Todas'))
    temp = jinja_env.get_template('ver_transacciones.html')
    return temp.render(items=items, start=start, end=end,
                       prod_id=prod_id, bodegas=bodegas, bodega_id=bodega_id)


@w.get('/app/ver_ventas')
@dbcontext
@auth_decorator
def sale_by_product():
    today = datetime.datetime.now()
    start, end = parse_start_end_date_with_default(
        request.query, today - datetime.timedelta(days=7), today)
    alm_id = int(request.query.get('almacen_id', 1))
    almacen = prodapi.get_store_by_id(alm_id)

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
    values = sorted(prods_sale.values(), key=lambda x: -x.cant * x.prod.precio1)
    for x in values:
        print x.serialize()
    return temp.render(items=values, start=start, end=end, almacen=almacen.nombre,
                       almacenes=prodapi.get_stores())


@w.get('/app/adv/producto/<pid>')
@dbcontext
@auth_decorator
def ver_prod_advanced(pid):
    session = sessionmanager.session
    prod = session.query(NProducto).filter_by(codigo=pid).first()
    contenidos = list(session.query(NContenido).filter_by(prod_id=pid))
    pricelist = list(session.query(NPriceList).filter(
        NPriceList.prod_id.in_((pid, pid + '+', pid + '-'))))

    temp = jinja_env.get_template('adv_producto.html')
    return temp.render(prod=prod, contenidos=contenidos, pricelist=pricelist)


@w.get('/app/edit_note/<uid>')
@dbcontext
@auth_decorator
def edit_note(uid):
    note = sessionmanager.session.query(NNota).filter_by(id=uid).first()
    temp = jinja_env.get_template('edit_note.html')
    return temp.render(note=note)


@w.post('/app/edit_note/<uid>')
@dbcontext
@auth_decorator
@actionlogged
def post_edit_note(uid):
    values = dict(request.forms)
    if values['payment_format'] not in PaymentFormat.names:
        return 'invalid payment format'
    for key in ('subtotal', 'total', 'tax', 'discount'):
        values[key] = int(values[key])
    sessionmanager.session.query(NNota).filter_by(id=uid).update(
        values)
    redirect(request.url)


@w.get('/app/ver_comentarios')
@dbcontext
@auth_decorator
def ver_comentarios():
    today = datetime.datetime.now() + datetime.timedelta(days=1)
    start, end = parse_start_end_date_with_default(
        request.query, today - datetime.timedelta(days=7), today)
    comments = list(sessionmanager.session.query(NComment).filter(
        NComment.timestamp >= start, NComment.timestamp < end).order_by(
        desc(NComment.timestamp)))
    obj_template = {
        ObjType.CHECK: '/app/ver_cheque/{}',
        ObjType.INV: '/app/nota/{}',
        ObjType.TRANS: '/app/ingreso/{}',
    }
    for c in comments:
        c.url = obj_template[c.objtype].format(c.objid)

    temp = jinja_env.get_template('ver_comentarios.html')
    return temp.render(comentarios=comments, start=start, end=end)

