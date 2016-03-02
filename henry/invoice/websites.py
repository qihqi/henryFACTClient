import datetime
from decimal import Decimal
from bottle import request, abort, redirect, response, Bottle

from henry.base.auth import get_user
from henry.base.common import parse_start_end_date
from henry.base.serialization import json_loads
from henry.base.session_manager import DBContext
from henry.config import jinja_env

from henry.accounting.acct_schema import NComment

from .coreschema import NNota
from .dao import Invoice
from henry.product.dao import Store
from .web import get_inv_db_instance

__author__ = 'han'


def make_invoice_wsgi(dbapi, auth_decorator, actionlogged, invapi, pedidoapi):
    w = Bottle()
    dbcontext = DBContext(dbapi.session)

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
        query = dbapi.db_session.query(NNota).filter(
            NNota.timestamp >= start, NNota.timestamp < end)
        if alm:
            query = query.filter_by(almacen_id=alm)
        temp = jinja_env.get_template('invoice/list_facturas.html')
        return temp.render(notas=query, start=start, end=end,
                           almacenes=dbapi.search(Store))

    @w.get('/app/eliminar_factura')
    @dbcontext
    @auth_decorator
    def eliminar_factura_form(message=None):
        almacenes = list(dbapi.search(Store))
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
        db_instance = get_inv_db_instance(dbapi.db_session, almacen_id, codigo)
        if db_instance is None:
            alm = dbapi.get(almacen_id, Store)
            db_instance = dbapi.db_session.query(NNota).filter_by(
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
        dbapi.db_session.add(comment)
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
        almacenes = list(dbapi.search(Store))
        temp = jinja_env.get_template('invoice/ver_factura_form.html')
        return temp.render(almacenes=almacenes, message=message)

    @w.get('/app/ver_factura')
    @dbcontext
    @auth_decorator
    def ver_factura():
        almacen_id = int(request.query.get('almacen_id'))
        codigo = request.query.get('codigo').strip()
        db_instance = get_inv_db_instance(dbapi.db_session,
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
            comments = list(dbapi.db_session.query(NComment).filter_by(
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