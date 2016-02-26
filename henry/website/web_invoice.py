import datetime
from decimal import Decimal

from bottle import request, abort, redirect, response, Bottle

from henry.base.auth import get_user
from henry.accounting.acct_schema import NComment
from henry.invoice.coreschema import NNota
from henry.users.schema import NUsuario
from henry.base.serialization import json_loads
from henry.config import jinja_env
from henry.invoice.dao import Invoice
from henry.dao.document import Status
from henry.accounting.reports import (get_notas_with_clients, split_records,
                                      payment_report)
from henry.base.common import parse_start_end_date

webinvoice = w = Bottle()


def get_inv_db_instance(session, almacen_id, codigo):
    return session.query(
        NNota.id, NNota.status, NNota.items_location).filter_by(
        almacen_id=almacen_id, codigo=codigo).first()


def make_invoice_wsgi(dbcontext, auth_decorator, storeapi,
                      sessionmanager, actionlogged, invapi, pedidoapi):
    @w.get('/app/resumen_form')
    @dbcontext
    @auth_decorator
    def resume_form():
        temp = jinja_env.get_template('invoice/resumen_form.html')
        stores = storeapi.search()
        users = list(sessionmanager.session.query(NUsuario))
        return temp.render(almacenes=stores, users=users)

    @w.get('/app/resumen')
    @dbcontext
    @auth_decorator
    def get_resumen():
        user = request.query.get('user')
        store = request.query.get('almacen_id')
        start, end = parse_start_end_date(request.query)

        if user is None or store is None:
            abort(400, 'Escoje usuario y almacen')
        if start is None or end is None:
            abort(400, 'Hay que ingresar las fechas')

        store = int(store)
        report = payment_report(sessionmanager.session, end, start, store)

        temp = jinja_env.get_template('invoice/resumen_nuevo.html')
        return temp.render(
            start=start,
            end=end,
            user=user,
            store=storeapi.get(store),
            report=report)

    @w.get('/app/resumen_viejo')
    @dbcontext
    @auth_decorator
    def get_resumen_viejo():
        user = request.query.get('user')
        store = request.query.get('almacen_id')
        start, end = parse_start_end_date(request.query)

        if user is None or store is None:
            abort(400, 'Escoje usuario y almacen')
        if start is None or end is None:
            abort(400, 'Hay que ingresar las fechas')

        store = int(store)
        session = sessionmanager.session
        result = get_notas_with_clients(session, end, start, store)

        by_status = split_records(result, lambda x: x.status)
        deleted = by_status[Status.DELETED]
        committed = by_status[Status.COMITTED]
        ventas = split_records(committed, lambda x: x.payment_format)

        gtotal = sum((x.total for x in committed))
        temp = jinja_env.get_template('invoice/resumen.html')
        return temp.render(
            start=start,
            end=end,
            user=user,
            store=storeapi.get(store),
            ventas=ventas,
            gtotal=gtotal,
            eliminados=deleted)

    @w.get('/app/list_facturas')
    @dbcontext
    @auth_decorator
    def list_facturas():
        start, end = parse_start_end_date(request.query)
        if not start:
            start = datetime.datetime.today() - datetime.timedelta(days=1)
        if not end:
            end = datetime.datetime.today()
        alm = request.query.almacen_id
        query = sessionmanager.session.query(NNota).filter(
            NNota.timestamp >= start, NNota.timestamp < end)
        if alm:
            query = query.filter_by(almacen_id=alm)
        temp = jinja_env.get_template('invoice/list_facturas.html')
        return temp.render(notas=query, start=start, end=end,
                           almacenes=storeapi.search())

    @w.get('/app/eliminar_factura')
    @dbcontext
    @auth_decorator
    def eliminar_factura_form(message=None):
        almacenes = list(storeapi.search())
        print almacenes
        temp = jinja_env.get_template('invoice/eliminar_factura.html')
        return temp.render(almacenes=almacenes, message=message)

    @w.post('/app/eliminar_factura')
    @dbcontext
    @auth_decorator
    @actionlogged
    def eliminar_factura():
        almacen_id = int(request.forms.get('almacen_id'))
        codigo = request.forms.get('codigo').strip()
        ref = request.forms.get('motivo')
        if not ref:
            abort(400, 'escriba el motivo')
        user = get_user(request)
        db_instance = get_inv_db_instance(sessionmanager.session, almacen_id, codigo)
        if db_instance is None:
            alm = storeapi.get(almacen_id)
            db_instance = sessionmanager.session.query(NNota).filter_by(
                almacen_ruc=alm.ruc, codigo=codigo).first()
        if db_instance is None:
            return eliminar_factura_form('Factura no existe')

        comment = NComment(
            user_id=user['username'],
            timestamp=datetime.datetime.now(),
            comment=ref,
            objtype='notas',
            objid=str(db_instance.id),
        )
        sessionmanager.session.add(comment)
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
        almacenes = list(storeapi.search())
        temp = jinja_env.get_template('invoice/ver_factura_form.html')
        return temp.render(almacenes=almacenes, message=message)

    @w.get('/app/ver_factura')
    @dbcontext
    @auth_decorator
    def ver_factura():
        almacen_id = int(request.query.get('almacen_id'))
        codigo = request.query.get('codigo').strip()
        db_instance = get_inv_db_instance(sessionmanager.session,
                                          almacen_id, codigo)
        if db_instance is None:
            return get_nota_form('Factura no existe')
        redirect('/app/nota/{}'.format(db_instance.id))

    @w.get('/app/nota/<uid>')
    @dbcontext
    @auth_decorator
    def get_nota(uid):
        doc = invapi.get_doc(uid)
        if doc:
            comments = list(sessionmanager.session.query(NComment).filter_by(
                objtype='notas', objid=doc.meta.uid))
            temp = jinja_env.get_template('invoice/nota.html')
            return temp.render(inv=doc, comments=comments)
        return 'Documento con codigo {} no existe'.format(uid)

    @w.get('/app/nota_de_pedido')
    @dbcontext
    @auth_decorator
    def get_notas_de_pedido_form():
        session = request.environ.get('beaker.session')
        if session is None or 'login_info' not in session:
            response.status = 401
            response.set_header('www-authenticate', 'Basic realm="Henry"')
            return ''
        temp = jinja_env.get_template('invoice/crear_pedido.html')
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
        temp = jinja_env.get_template('invoice/ver_pedido.html')
        return temp.render(pedido=pedido, willprint=willprint)

    return w
