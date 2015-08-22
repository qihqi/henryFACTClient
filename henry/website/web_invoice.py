import datetime
from decimal import Decimal
from operator import attrgetter

from bottle import request, abort, redirect, response, Bottle

from henry.base.auth import get_user
from henry.schema.meta import NComment
from henry.schema.account import NAccountStat, NPayment, NSpent
from henry.schema.core import NNota, NUsuario
from henry.base.serialization import json_loads
from henry.config import (dbcontext, auth_decorator, jinja_env, prodapi,
                          sessionmanager, actionlogged, invapi, pedidoapi)
from henry.dao import Status, PaymentFormat, Invoice
from henry.website.reports import (get_notas_with_clients, split_records,
                                   group_by_records, payment_report)
from henry.website.common import parse_start_end_date, parse_iso

webinvoice = w = Bottle()


def get_inv_db_instance(session, almacen_id, codigo):
    return session.query(
        NNota.id, NNota.status, NNota.items_location).filter_by(
        almacen_id=almacen_id, codigo=codigo).first()


@w.get('/app/resumen_form')
@dbcontext
@auth_decorator
def resume_form():
    temp = jinja_env.get_template('invoice/resumen_form.html')
    stores = prodapi.get_stores()
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
        store=prodapi.get_store_by_id(store),
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
        store=prodapi.get_store_by_id(store),
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
    return temp.render(notas=query, start=start, end=end, almacenes=prodapi.get_stores())


@w.get('/app/eliminar_factura')
@dbcontext
@auth_decorator
def eliminar_factura_form(message=None):
    almacenes = list(prodapi.get_stores())
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

    comment = NComment(
        user_id=user['username'],
        timestamp=datetime.datetime.now(),
        comment=ref,
        objtype='notas',
        objid=str(db_instance.id),
    )
    sessionmanager.session.add(comment)
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


@w.get('/app/entregar_cuenta_form')
@dbcontext
@auth_decorator
def entrega_de_cuenta():
    temp = jinja_env.get_template('invoice/entregar_cuenta_form.html')
    return temp.render()


@w.get('/app/crear_entrega_de_cuenta')
@dbcontext
@auth_decorator
def crear_entrega_de_cuenta():
    date = request.query.get('fecha')
    if date:
        date = parse_iso(date).date()
    else:
        date = datetime.date.today()

    all_sale = list(get_notas_with_clients(sessionmanager.session, date, date))
    split_by_status = split_records(all_sale, lambda x: x.status == Status.DELETED)
    deleted = split_by_status[True]
    other = split_by_status[False]
    split_by_cash = split_records(other, lambda x: x.payment_format == PaymentFormat.CASH)
    cashed = split_by_cash[True]
    noncash = split_by_cash[False]
    sale_by_store = group_by_records(cashed, attrgetter('almacen_name'), attrgetter('total'))

    ids = [c.uid for c in all_sale]
    cashids = {c.uid for c in cashed}
    noncash = split_records(noncash, lambda x: x.client.codigo)
    query = sessionmanager.session.query(NPayment).filter(NPayment.note_id.in_(ids))

    # only retension for cash invoices need to be accounted separately.
    by_retension = split_records(query, lambda x: x.type == 'retension' and x.note_id in cashids)
    other_cash = sum((x.value for x in by_retension[False] if x.type == PaymentFormat.CASH))
    total_cash = sum(sale_by_store.values()) + other_cash
    payments = split_records(by_retension[False], attrgetter('client_id'))
    retension = by_retension[True]

    all_spent = list(sessionmanager.session.query(NSpent).filter(
        NSpent.inputdate >= date, NSpent.inputdate < date + datetime.timedelta(days=1)))
    total_spent = sum((x.paid_from_cashier for x in all_spent))
    existing = sessionmanager.session.query(NAccountStat).filter_by(date=date).first()
    temp = jinja_env.get_template('invoice/crear_entregar_cuenta_form.html')
    return temp.render(
        cash=sale_by_store, others=noncash,
        total_cash=total_cash,
        deleted=deleted,
        date=date.isoformat(),
        pagos=payments,
        all_spent=all_spent,
        total_spent=total_spent,
        retension=retension,
        other_cash=other_cash,
        existing=existing)



@w.post('/app/crear_entrega_de_cuenta')
@dbcontext
@auth_decorator
def post_crear_entrega_de_cuenta():
    cash = request.forms.get('cash', 0)
    gastos = request.forms.get('gastos', 0)
    deposito = request.forms.get('deposito', 0)
    turned_cash = request.forms.get('valor', 0)
    date = request.forms.get('date')

    cash = int(float(cash) * 100)
    gastos = int(float(gastos) * 100)
    deposito = int(float(deposito) * 100)
    turned_cash = int(float(turned_cash) * 100)
    date = parse_iso(date).date()

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
                {'revised_by': userid, 'turned_cash': turned_cash, 'deposit': deposito})
    redirect('/app/crear_entrega_de_cuenta?fecha={}'.format(date.isoformat()))


@w.get('/app/entrega_de_cuenta_list')
@dbcontext
@auth_decorator
def ver_entrega_de_cuenta_list():
    start, end = parse_start_end_date(request.query)
    if end is None:
        end = datetime.date.today()
    if start is None:
        start = datetime.date.today() - datetime.timedelta(days=7)

    accts = sessionmanager.session.query(NAccountStat).filter(
        NAccountStat.date >= start, NAccountStat.date <= end)
    temp = jinja_env.get_template('invoice/entrega_de_cuenta_list.html')
    return temp.render(accts=accts, start=start, end=end)


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
