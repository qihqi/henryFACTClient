from __future__ import print_function
from builtins import str
import datetime
import traceback
from typing import Callable

from bottle import Bottle, request, abort, redirect, json_loads

from henry.base.dbapi import DBApiGeneric

from henry.base.auth import AuthType
from henry.base.common import parse_start_end_date
from henry.base.serialization import json_dumps
from henry.base.session_manager import DBContext
from henry.common import transmetadata_from_form, items_from_form
from henry.dao.document import Status, DocumentApi

from henry.product.dao import Bodega

from .dao import TransType, Transferencia, TransMetadata


def make_inv_api(dbapi: DBApiGeneric,
                 transapi: DocumentApi,
                 auth_decorator: AuthType,
                 actionlogged: Callable[[Callable], Callable],
                 forward_transaction):
    api = Bottle()
    dbcontext = DBContext(dbapi.session)

    @api.post('/app/api/ingreso')
    @dbcontext
    @auth_decorator(0)
    @actionlogged
    def crear_ingreso():
        json_content = request.body.read()
        json_dict = json_loads(json_content)
        ingreso = Transferencia.deserialize(json_dict)
        ingreso = transapi.save(ingreso)
        return {'codigo': ingreso.meta.uid}

    @api.put('/app/api/ingreso/<ingreso_id>')
    @dbcontext
    @auth_decorator(0)
    @actionlogged
    def postear_ingreso(ingreso_id):
        trans = transapi.get_doc(ingreso_id)
        transapi.commit(trans)
        if forward_transaction is not None:
            if trans.meta.trans_type == TransType.EXTERNAL:
                trans.meta.dest = 4  # policentro
                trans.meta.trans_type = TransType.TRANSFER
        return {'status': trans.meta.status}

    @api.delete('/app/api/ingreso/<ingreso_id>')
    @dbcontext
    @actionlogged
    def delete_ingreso(ingreso_id):
        trans = transapi.get_doc(ingreso_id)
        old_status = trans.meta.status
        transapi.delete(trans)
        return {'status': trans.meta.status}

    @api.get('/app/api/ingreso/<ingreso_id>')
    @dbcontext
    @actionlogged
    def get_ingreso(ingreso_id):
        ing = transapi.get_doc(ingreso_id)
        if ing is None:
            abort(404, 'Ingreso No encontrada')
            return
        return json_dumps(ing.serialize())

    @api.get('/app/api/ingreso')
    @dbcontext
    @actionlogged
    def get_trans_by_date():
        start, end = parse_start_end_date(
            request.query, start_name='start_date', end_name='end_date')
        status = request.query.get('status')
        other_filters = {}
        for x in ('origin', 'dest'):
            t = request.query.get(x)
            if t:
                other_filters[x] = t
        result = transapi.search_metadata_by_date_range(
            start, end, status, other_filters)
        return json_dumps(list(result))

    return api


def make_inv_wsgi(
        dbapi: DBApiGeneric, jinja_env,
        actionlogged: Callable[[Callable], Callable],
        auth_decorator: AuthType, transapi: DocumentApi,
        revisionapi, external_bodegas):
    w = Bottle()
    dbcontext = DBContext(dbapi.session)

    @w.get('/app/ver_ingreso_form')
    @dbcontext
    @auth_decorator(0)
    def ver_ingreso_form():
        return jinja_env.get_template('inventory/ver_ingreso_form.html').render()

    @w.get('/app/ingreso/<uid>')
    @dbcontext
    @auth_decorator(0)
    def get_ingreso(uid):
        trans = transapi.get_doc(uid)
        if not trans:
            return 'Documento con codigo {} no existe'.format(uid)
        temp = jinja_env.get_template('inventory/ingreso.html')
        if trans.meta.origin is not None:
            trans.meta.origin = dbapi.get(trans.meta.origin, Bodega).nombre
        if trans.meta.dest is not None:
            trans.meta.dest = dbapi.get(trans.meta.dest, Bodega).nombre
        return temp.render(ingreso=trans)

    @w.get('/app/crear_ingreso')
    @dbcontext
    @auth_decorator(0)
    def crear_ingreso():
        temp = jinja_env.get_template('inventory/crear_ingreso.html')
        bodegas = dbapi.search(Bodega)
        bodegas_externas = [Bodega(id=i, nombre=n[0])
                            for i, n in enumerate(external_bodegas)]
        return temp.render(bodegas=bodegas, externas=bodegas_externas,
                           types=TransType.names)

    def remove_upi(items):
        for i in items:
            i.prod.upi = None

    @w.post('/app/crear_ingreso')
    @dbcontext
    @auth_decorator(0)
    @actionlogged
    def post_crear_ingreso():
        meta = transmetadata_from_form(request.forms)
        items = items_from_form(dbapi, request.forms)
        meta.value = sum((x.cant * (x.prod.base_price_usd or 0) for x in items))
        try:
            transferencia = Transferencia(meta, items)
            if meta.trans_type == TransType.EXTERNAL:
                newmeta = TransMetadata().merge_from(meta)
                external_bodega_index = int(request.forms['externa'])
                _, api, dest_id = external_bodegas[external_bodega_index]
                newmeta.dest = dest_id
                newmeta.origin = None
                newmeta.trans_type = TransType.INGRESS
                remove_upi(items)
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
    @auth_decorator(0)
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
        bodega = {b.id: b.nombre for b in dbapi.search(Bodega)}
        print(start, end)
        return temp.render(trans=trans_list, start=start, end=end, bodega=bodega)

    @w.get('/app/revisar_inventario')
    @dbcontext
    @auth_decorator(0)
    def revisar_inv_form():
        temp = jinja_env.get_template('inventory/crear_revision.html')
        return temp.render(bodegas=dbapi.search(Bodega))

#    @w.post('/app/revisar_inventario')
#    @dbcontext
#    @auth_decorator(0)
#    def post_revisar_inv():
#        bodega_id = request.forms.get('bodega_id', None)
#        if bodega_id is None:
#            abort(400, 'bodega_id no existe')
#        prod_ids = request.forms.getlist('prod_id')
#        rev = revisionapi.save(bodega_id, get_user(request)['username'], prod_ids)
#        redirect('/app/revision/{}'.format(rev.uid))
#
#    @w.get('/app/revision/<rid>')
#    @dbcontext
#    @auth_decorator(0)
#    def get_revision(rid):
#        meta = revisionapi.get(rid)
#        bodega_name = dbapi.get(meta.bodega_id, Bodega).nombre
#        items = []
#        for y in meta.items:
#            item = dbapi.getone(ProdCount,
#                                prod_id=y.prod_id, bodega_id=meta.bodega_id)
#            name = dbapi.getone(Product, codigo=y.prod_id).nombre
#            item.nombre = name
#            if y.inv_cant:
#                item.cantidad = y.inv_cant
#            if y.real_cant is not None:
#                item.contado = y.real_cant
#            items.append(item)
#
#        temp = jinja_env.get_template('inventory/revision.html')
#        return temp.render(meta=meta, items=items, bodega_name=bodega_name)
#
#    @w.post('/app/revision/<rid>')
#    @dbcontext
#    @auth_decorator(0)
#    def post_revision(rid):
#        prods = {}
#        for key, value in request.forms.items():
#            prods[key.replace('prod-cant-', '')] = value
#        revisionapi.update_count(rid, prods)
#        redirect('/app/revision/{}'.format(rid))
#
#    @w.get('/app/list_revision')
#    @dbcontext
#    @auth_decorator(0)
#    def list_revision():
#        start, end = parse_start_end_date(request.query)
#        if end is None:
#            end = datetime.datetime.now()
#        if start is None:
#            start = end - datetime.timedelta(days=7)
#
#        revisions = dbapi.db_session.query(NInventoryRevision).filter(
#            NInventoryRevision.timestamp <= end,
#            NInventoryRevision.timestamp >= start)
#
#        temp = jinja_env.get_template('inventory/list_revisions.html')
#        return temp.render(revisions=revisions, start=start, end=end)
#
#    @w.get('/app/revisiones')
#    @dbcontext
#    @auth_decorator(0)
#    def revisiones_main():
#        user = get_user(request)
#        if 'level' not in user:
#            userdb = dbapi.db_session.query(
#                NUsuario).filter(NUsuario.username == user['username']).first()
#            user['level'] = userdb.level
#            beaker = request.environ['beaker.session']
#            beaker['login_info'] = user
#            beaker.save()
#        level = user['level']
#        print level
#        if level < 2:
#            return 'no autorizado'
#        temp = jinja_env.get_template('inventory/revisiones.html')
#        return temp.render()

    return w
