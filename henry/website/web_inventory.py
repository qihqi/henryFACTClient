import traceback
import datetime

from bottle import request, Bottle, abort, redirect
from decimal import Decimal
from henry.base.auth import get_user

from henry.config import jinja_env, prodapi, actionlogged, transapi, BODEGAS_EXTERNAS, sessionmanager, revisionapi
from henry.config import (dbcontext, auth_decorator)
from henry.dao import TransType, TransMetadata, Transferencia
from henry.dao.productos import Bodega
from henry.website.common import items_from_form, transmetadata_from_form, parse_start_end_date
from henry.base.schema import NInventoryRevision, NInventoryRevisionItem

w = Bottle()
web_inventory_webapp = w


@w.get('/app/ver_ingreso_form')
@dbcontext
@auth_decorator
def ver_ingreso_form():
    return jinja_env.get_template('inventory/ver_ingreso_form.html').render()


@w.get('/app/ver_cantidad')
@dbcontext
@auth_decorator
def ver_cantidades():
    bodega_id = int(request.query.get('bodega_id', 1))
    prefix = request.query.get('prefix', None)
    if prefix:
        all_prod = prodapi.search_prod_cant(prefix, bodega_id)
    else:
        all_prod = []
    temp = jinja_env.get_template('inventory/ver_cantidad.html')
    return temp.render(prods=all_prod, bodegas=prodapi.get_bodegas(),
                       prefix=prefix, bodega_name=prodapi.get_bodega_by_id(bodega_id).nombre)


@w.get('/app/ingreso/<uid>')
@dbcontext
@auth_decorator
def get_ingreso(uid):
    trans = transapi.get_doc(uid)
    if not trans:
        return 'Documento con codigo {} no existe'.format(uid)
    temp = jinja_env.get_template('inventory/ingreso.html')
    if trans.meta.origin is not None:
        trans.meta.origin = prodapi.get_bodega_by_id(trans.meta.origin).nombre
    if trans.meta.dest is not None:
        trans.meta.dest = prodapi.get_bodega_by_id(trans.meta.dest).nombre
    return temp.render(ingreso=trans)


@w.get('/app/crear_ingreso')
@dbcontext
@auth_decorator
def crear_ingreso():
    temp = jinja_env.get_template('inventory/crear_ingreso.html')
    bodegas = prodapi.get_bodegas()
    bodegas_externas = [Bodega(id=i, nombre=n[0]) for i, n in enumerate(BODEGAS_EXTERNAS)]
    return temp.render(bodegas=bodegas, externas=bodegas_externas,
                       types=TransType.names)


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


@w.get('/app/ingresos_list')
@dbcontext
@auth_decorator
def list_ingress():
    start, end = parse_start_end_date(request.query)
    if not end:
        end = datetime.datetime.now()
    else:
        end = end + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
    if not start:
        start = end - datetime.timedelta(days=7)
    trans_list = transapi.search_metadata_by_date_range(start, end)
    temp = jinja_env.get_template('inventory/ingresos_list.html')
    bodega = {b.id: b.nombre for b in prodapi.get_bodegas()}
    print start, end
    return temp.render(trans=trans_list, start=start, end=end, bodega=bodega)


@w.get('/app/revisar_inventario')
@dbcontext
@auth_decorator
def revisar_inv_form():
    temp = jinja_env.get_template('inventory/crear_revision.html')
    return temp.render(bodegas=prodapi.get_bodegas())


@w.post('/app/revisar_inventario')
@dbcontext
@auth_decorator
def post_revisar_inv():
    bodega_id = request.forms.get('bodega_id', None)
    if bodega_id is None:
        abort(400, 'bodega_id no existe')
    prod_ids = request.forms.getlist('prod_id')
    rev = revisionapi.save(bodega_id, get_user(request)['username'], prod_ids)
    redirect('/app/revision/{}'.format(rev.uid))


@w.get('/app/revision/<rid>')
@dbcontext
@auth_decorator
def get_revision(rid):
    meta = revisionapi.get(rid)
    bodega_name = prodapi.get_bodega_by_id(meta.bodega_id).nombre
    items = []
    for y in meta.items:
        item = prodapi.get_cant(prod_id=y.prod_id, bodega_id=meta.bodega_id)
        item.cantidad = y.inv_cant
        if y.real_cant is not None:
            item.contado = y.real_cant
        items.append(item)

    temp = jinja_env.get_template('inventory/revision.html')
    return temp.render(meta=meta, items=items, bodega_name=bodega_name)


@w.post('/app/revision/<rid>')
@dbcontext
@auth_decorator
def get_revision(rid):
    prods = {}
    for key, value in request.forms.items():
        prods[key.replace('prod-cant-', '')] = value
    revisionapi.update_count(rid, prods)
    redirect('/app/revision/{}'.format(rid))

@w.get('/app/list_revision')
@dbcontext
@auth_decorator
def list_revision():
    start, end = parse_start_end_date(request.query)
    if end is None:
        end = datetime.datetime.now()
    if start is None:
        start = end - datetime.timedelta(days=7)

    revisions = sessionmanager.session.query(NInventoryRevision).filter(
        NInventoryRevision.timestamp <= end, NInventoryRevision.timestamp >= start)

    temp = jinja_env.get_template('inventory/list_revisions.html')
    return temp.render(revisions=revisions, start=start, end=end)
