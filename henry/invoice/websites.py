import io
import datetime
import json
from operator import itemgetter
import os
import zipfile

from bottle import request, response, abort, redirect, Bottle
import barcode

from henry.base.auth import get_user
from henry.base.common import parse_start_end_date
from henry.base.serialization import json_dumps
from henry.base.session_manager import DBContext
from henry.dao.document import Status
from henry.users.dao import Client

from henry.accounting.acct_schema import NPayment
from henry.product.dao import Store
from henry.accounting.dao import Comment
from henry.invoice.dao import PaymentFormat, InvMetadata, SRINota, Invoice

from .coreschema import NNota
from .schema import NSRINota
from .coreapi import get_inv_db_instance
from .util import get_or_generate_xml_paths

__author__ = 'han'


def make_invoice_wsgi(dbapi, auth_decorator, actionlogged, invapi, pedidoapi, jinja_env, workqueue, file_manager):
    w = Bottle()
    dbcontext = DBContext(dbapi.session)

    @w.get('/app/list_facturas')
    @dbcontext
    @auth_decorator(0)
    def list_facturas():
        start, end = parse_start_end_date(request.query)
        if not start:
            start = datetime.datetime.today() - datetime.timedelta(days=1)
        if not end:
            end = datetime.datetime.today()
        alm = request.query.almacen_id
        query = dbapi.db_session.query(NNota).filter(
            NNota.timestamp >= start, NNota.timestamp < end)
        if alm:
            query = query.filter_by(almacen_id=alm)
        temp = jinja_env.get_template('invoice/list_facturas.html')
        return temp.render(notas=query, start=start, end=end,
                           almacenes=dbapi.search(Store))

    @w.get('/app/eliminar_factura')
    @dbcontext
    @auth_decorator(1)
    def eliminar_factura_form(message=None):
        almacenes = list(dbapi.search(Store))
        temp = jinja_env.get_template('invoice/eliminar_factura.html')
        return temp.render(almacenes=almacenes, message=message)

    @w.post('/app/eliminar_factura')
    @dbcontext
    @auth_decorator(1)
    @actionlogged
    def eliminar_factura():
        almacen_id = int(request.forms.get('almacen_id'))
        codigo = request.forms.get('codigo').strip()
        ref = request.forms.get('motivo')
        if not ref:
            abort(400, 'escriba el motivo')
        user = get_user(request)

        inv_meta = dbapi.getone(InvMetadata, almacen_id=almacen_id, codigo=codigo)
        if inv_meta is None:
            alm = dbapi.get(almacen_id, Store)
            inv_meta = dbapi.getone(InvMetadata, almacen_ruc=alm.ruc, codigo=codigo)
        if inv_meta is None:
            return eliminar_factura_form('Factura no existe')

        if inv_meta.status == Status.DELETED:
            # already deleted
            redirect('/app/nota/{}'.format(inv_meta.uid))

        comment = Comment(
            user_id=user['username'],
            timestamp=datetime.datetime.now(),
            comment=ref,
            objtype='notas',
            objid=str(inv_meta.uid),
        )
        dbapi.create(comment)
        doc = invapi.get_doc_from_file(inv_meta.items_location)
        doc.meta.status = inv_meta.status

        try:
            invapi.delete(doc)
        except ValueError:
            abort(400)

        redirect('/app/nota/{}'.format(inv_meta.uid))

    @w.get('/app/ver_factura_form')
    @dbcontext
    @auth_decorator(0)
    def get_nota_form(message=None):
        almacenes = list(dbapi.search(Store))
        temp = jinja_env.get_template('invoice/ver_factura_form.html')
        return temp.render(almacenes=almacenes, message=message)

    @w.get('/app/ver_factura')
    @dbcontext
    @auth_decorator(0)
    def ver_factura():
        almacen_id = int(request.query.get('almacen_id'))
        codigo = request.query.get('codigo').strip()
        db_instance = get_inv_db_instance(dbapi.db_session,
                                          almacen_id, codigo)
        if db_instance is None:
            return get_nota_form('Factura no existe')
        redirect('/app/nota/{}'.format(db_instance.uid))

    @w.get('/app/nota/<uid>')
    @dbcontext
    @auth_decorator(0)
    def get_nota(uid):
        doc = invapi.get_doc(uid)
        if doc:
            comments = dbapi.search(Comment, objtype='notas', objid=doc.meta.uid)
            temp = jinja_env.get_template('invoice/nota.html')
            return temp.render(inv=doc, comments=comments)
        return 'Documento con codigo {} no existe'.format(uid)

    @w.get('/app/api/nota')
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
        client = request.query.get('client')
        other_filters = {'client_id', client} if client else None
        result = invapi.search_metadata_by_date_range(
            start_date, end_date, status, other_filters)
        return json_dumps(list(result))

    @w.get('/app/client_stat/<uid>')
    @dbcontext
    @auth_decorator(0)
    def get_client_stat(uid):
       end_date = datetime.datetime.now()
       start_date = end_date - datetime.timedelta(days=365)
       status = Status.COMITTED

       result = list(invapi.search_metadata_by_date_range(
           start_date, end_date, status, {'client_id': uid}))
       payments = list(dbapi.db_session.query(NPayment).filter(
           NPayment.client_id == uid))

       all_data = [('COMPRA', r.uid, r.timestamp.date(), '', r.total / 100)
                   for r in result if r.payment_format != PaymentFormat.CASH]
       all_data.extend((('PAGO ' + r.type, r.uid, r.date, r.value/ 100, '') for r in payments))
       all_data.sort(key=itemgetter(2), reverse=True)

       compra = sum(r.total for r in result if r.payment_format != PaymentFormat.CASH)/ 100
       pago = sum(r.value for r in payments)/ 100

       temp = jinja_env.get_template('client_stat.html')
       client = dbapi.get(uid, Client) # clientapi.get(uid)
       return temp.render(client=client, activities=all_data, compra=compra, pago=pago)


    def sri_nota_to_nota_and_extra(sri_nota):
        json_env = json.loads(
            file_manager.get_file(sri_nota.json_inv_location))
        doc = Invoice.deserialize(json_env)
        if not doc:
            abort(404, 'Documento con codigo {} no existe'.format(uid))

        bcode = barcode.Gs1_128(sri_nota.access_code)
        svg_code = bcode.render().decode('utf-8')
        index = svg_code.find('<svg')
        svg_code = svg_code[index:]
        extra = {
            'ambiente': 'ambiente',
            'direccion': 'direction',
            'access_code': sri_nota.access_code,
            'svg_code': svg_code
        }
        return doc, extra

    @w.get('/app/factura/<uid>')
    @dbcontext
    @auth_decorator(0)
    def get_nota_print(uid):
        sri_nota = dbapi.get(uid, SRINota)
        doc, extra = sri_nota_to_nota_and_extra(sri_nota)
        if doc:
            temp = jinja_env.get_template('invoice/nota_impreso.html')
            return temp.render(inv=doc, extra=extra)
        return 'Documento con codigo {} no existe'.format(uid)



    @w.get('/app/alm/<alm_ruc>/ultima_factura')
    @dbcontext
    @auth_decorator(0)
    def last_inv_print(alm_ruc):
        nsri_nota = dbapi.db_session.query(NSRINota).filter(
            NSRINota.almacen_ruc == alm_ruc).order_by(
            NSRINota.timestamp_received.desc()).first()

        if nsri_nota is None:
            abort(404, 'No existe')

        sri_nota = SRINota.from_db_instance(nsri_nota)
        doc, extra = sri_nota_to_nota_and_extra(sri_nota)

        print(sri_nota.serialize())
        temp = jinja_env.get_template('invoice/nota_impreso.html')
        response.headers['Cache-Control'] = 'no-cache'
        return temp.render(inv=doc, extra=extra)

    @w.get('/app/exportar_facturas')
    @dbcontext
    @auth_decorator(0)
    def export_inv_view():
        start, end = parse_start_end_date(request.query)
        if not start:
            start = datetime.datetime.today() - datetime.timedelta(days=1)
        if not end:
            end = datetime.datetime.today()
        alm = request.query.almacen_id
        query = dbapi.db_session.query(NSRINota).filter(
            NSRINota.orig_timestamp >= start, NSRINota.orig_timestamp <= end)
        almacenes = dbapi.search(Store)
        alm_ruc = None
        if alm:
            alm_obj = dbapi.get(alm, Store)
            alm_ruc = alm_obj.ruc
            query = query.filter_by(almacen_ruc=alm_ruc)
        notas = sorted(query, key=lambda x: x.uid)
        min_id, max_id = None, None
        if notas:
            min_id = notas[0].uid
            max_id = notas[-1].uid
        temp = jinja_env.get_template('invoice/buscar_export_factura.html')
        return temp.render(sri_notas=notas, start=start, end=end,
                           almacenes=almacenes, min_id=min_id, max_id=max_id,
                           alm_ruc=alm_ruc)

    @w.post('/app/exportar_facturas')
    @dbcontext
    @auth_decorator(0)
    def export_inv_real():
        start_id = int(request.forms.get('start_id'))
        end_id = int(request.forms.get('end_id'))
        ruc = request.forms.get('almacen_ruc')
        query = dbapi.db_session.query(NSRINota).filter(
            NSRINota.uid >= start_id, NSRINota.uid <= end_id)

        content = io.BytesIO()
        with zipfile.ZipFile(content, 'w') as zfile:
            for k in query:
                sri_nota = SRINota.from_db_instance(k)
                relpath, signed_path = get_or_generate_xml_paths(sri_nota, file_manager, jinja_env, dbapi)
                fullpath = file_manager.make_fullpath(signed_path)
                name = os.path.basename(fullpath)
                zfile.write(fullpath, arcname=name)
        print(len(content.getbuffer()))
        content.seek(0)
        response.headers['Content-Type'] = 'application/zip'
        response.headers['Content-Disposition'] = 'attachment; filename="{}-{}.zip"'.format(start_id, end_id)
        return content





    return w
