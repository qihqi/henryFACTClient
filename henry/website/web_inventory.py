import traceback

from bottle import request, Bottle, abort, redirect

from henry.config import jinja_env, prodapi, actionlogged, transapi, BODEGAS_EXTERNAS
from henry.config import (dbcontext, auth_decorator)
from henry.dao import TransType, TransMetadata, Transferencia
from henry.dao.productos import Bodega
from henry.website.common import items_from_form, transmetadata_from_form

w = Bottle()
web_inventory_webapp = w


@w.get('/app/ver_ingreso_form')
@dbcontext
@auth_decorator
def ver_ingreso_form():
    return jinja_env.get_template('ver_ingreso_form.html').render()


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
    temp = jinja_env.get_template('ver_cantidad.html')
    return temp.render(prods=all_prod, bodegas=prodapi.get_bodegas(),
                       prefix=prefix, bodega_name=prodapi.get_bodega_by_id(bodega_id).nombre)


@w.get('/app/ingreso/<uid>')
@dbcontext
@auth_decorator
def get_ingreso(uid):
    trans = transapi.get_doc(uid)
    if not trans:
        return 'Documento con codigo {} no existe'.format(uid)
    temp = jinja_env.get_template('ingreso.html')
    if trans.meta.origin is not None:
        trans.meta.origin = prodapi.get_bodega_by_id(trans.meta.origin).nombre
    if trans.meta.dest is not None:
        trans.meta.dest = prodapi.get_bodega_by_id(trans.meta.dest).nombre
    return temp.render(ingreso=trans)


@w.get('/app/crear_ingreso')
@dbcontext
@auth_decorator
def crear_ingreso():
    temp = jinja_env.get_template('crear_ingreso.html')
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
