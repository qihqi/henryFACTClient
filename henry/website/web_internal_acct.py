import datetime
from decimal import Decimal
import os
import uuid
from bottle import request, redirect, static_file, Bottle
from henry.base.auth import get_user
from henry.schema.meta import ObjType, NComment
from henry.schema.account import NCheck, SpentType, NSpent
from henry.schema.core import NNota
from henry.config import jinja_env, dbcontext, auth_decorator, paymentapi, sessionmanager, imagefiles, prodapi
from henry.dao import PaymentFormat
from henry.dao.payment import Check, Deposit, Payment
from henry.website.common import parse_iso, parse_start_end_date_with_default

w = internal_acct = Bottle()


def render_form_with_msg(path, title):
    msg = request.query.msg
    temp = jinja_env.get_template(path)
    return temp.render(msg=msg, title=title)


@w.get('/app/crear_cuenta_form')
@dbcontext
@auth_decorator
def create_cuenta():
    return render_form_with_msg(
        'invoice/crear_banco_form.html', title='Crear Cuenta')


@w.get('/app/crear_banco_form')
@dbcontext
@auth_decorator
def create_bank():
    return render_form_with_msg(
        'invoice/crear_banco_form.html', title='Crear Banco')


@w.post('/app/crear_banco_form')
@dbcontext
@auth_decorator
def post_create_bank():
    name = request.forms.name
    paymentapi.create_account(name)
    redirect('/app/crear_banco_form?msg=Cuenta+Creada')


@w.post('/app/crear_cuenta_form')
@dbcontext
@auth_decorator
def post_create_cuenta():
    name = request.forms.name
    paymentapi.create_account(name)
    redirect('/app/crear_banco_form?msg=Cuenta+Creada')


@w.post('/app/guardar_cheque_deposito')
@dbcontext
@auth_decorator
def post_guardar_cheque_deposito():
    nexturl = request.forms.get('next', '/app')
    for key, value in request.forms.items():
        print key, value
        if key.startswith('acct-'):
            key = key.replace('acct-', '')
            print key, value
            sessionmanager.session.query(NCheck).filter_by(uid=key).update(
                {NCheck.deposit_account: value})
            sessionmanager.session.flush()
    redirect(nexturl)


@w.get('/app/ver_cheque/<cid>')
@dbcontext
@auth_decorator
def ver_cheque(cid):
    check = paymentapi.get_check(cid)
    if check.imgcheck:
        _, check.imgcheck = os.path.split(check.imgcheck)
    if check.imgdeposit:
        _, check.imgdeposit = os.path.split(check.imgdeposit)
    temp = jinja_env.get_template('invoice/ver_cheque.html')
    comments = list(sessionmanager.session.query(NComment).filter_by(
        objtype=ObjType.CHECK, objid=str(cid)))
    return temp.render(check=check, comments=comments)


@w.post('/app/postregar_cheque')
@dbcontext
@auth_decorator
def postregar_cheque():
    checkid = request.forms.checkid
    new_date = parse_iso(request.forms.new_date).date()
    session = sessionmanager.session
    check = session.query(NCheck).filter_by(uid=checkid).first()
    comment = NComment(
        timestamp=datetime.datetime.now(),
        user_id=get_user(request)['username'],
        comment='Cheque postponer desde {} hasta {}'.format(
            check.checkdate.isoformat(), new_date.isoformat()),
        objtype=ObjType.CHECK,
        objid=str(checkid),
    )
    session.add(comment)
    check.checkdate = new_date
    session.flush()
    redirect('/app/ver_cheque/{}'.format(checkid))


@w.post('/app/save_check_img/<imgtype>/<cid>')
@dbcontext
@auth_decorator
def save_check_image(cid, imgtype):
    upload = request.files.get('imgcheck')
    _, ext = os.path.splitext(upload.raw_filename)
    filename = uuid.uuid1().hex + ext
    filename = imagefiles.make_fullpath(filename)
    if save_check_image.image is None:
        try:
            from PIL import Image
            save_check_image.image = Image
        except ImportError:
            return 'Image module not installed'
    im = save_check_image.image.open(upload.file)
    if im.size[0] > 1024:
        im.resize((1024, 768))
    im.save(filename)

    if imgtype == 'deposit':
        row = NCheck.imgdeposit
        newstatus = 'DEPOSITADO'
    else:
        row = NCheck.imgcheck
        newstatus = 'RECIBIDO'
    sessionmanager.session.query(NCheck).filter_by(
        uid=cid).update({row: filename, NCheck.status: newstatus})
    redirect('/app/ver_cheque/{}'.format(cid))
save_check_image.image = None


@w.get('/app/imgcheck/<cid>')
@dbcontext
@auth_decorator
def check_image_get(cid):
    check = paymentapi.get_check(cid)
    return static_file(check.imgcheck, root='.')


@w.get('/app/guardar_deposito')
@dbcontext
@auth_decorator
def guardar_deposito():
    msg = request.query.msg
    temp = jinja_env.get_template('invoice/save_deposito_form.html')
    return temp.render(cuentas=paymentapi.get_all_accounts(),
                       stores=prodapi.get_stores(),
                       msg=msg)


def extract_nota_and_client(form, redirect_url):
    codigo = form.get('codigo')
    almacen = form.get('almacen_id')
    if codigo:
        nota = sessionmanager.session.query(NNota).filter_by(
            codigo=codigo, almacen_id=almacen).first()
        if nota is None:
            redirect('{}?msg=Orden+Despacho+No+{}+no+existe'.format(redirect_url, codigo))
        return nota.id, nota.client_id
    return None, None


@w.get('/app/guardar_cheque')
@dbcontext
@auth_decorator
def save_check_form():
    msg = request.query.msg
    temp = jinja_env.get_template('invoice/save_check_form.html')
    return temp.render(banks=paymentapi.get_all_banks(),
                       stores=prodapi.get_stores(),
                       msg=msg)


def parse_payment_from_request(form, clazz, url):
    date = datetime.date.today()
    if request.forms.ingresado == 'ayer':
        date = date - datetime.timedelta(days=1)
    payment = clazz.deserialize(request.forms)
    payment.note_id, payment.client_id = extract_nota_and_client(form, url)
    payment.value = int(Decimal(payment.value) * 100)
    payment.date = date
    return payment


@w.post('/app/guardar_cheque')
@dbcontext
@auth_decorator
def save_check():
    check = parse_payment_from_request(request.forms, Check, '/app/guardar_cheque')
    check.checkdate = parse_iso(check.checkdate)
    paymentapi.save_payment(check, PaymentFormat.CHECK)
    redirect('/app/guardar_cheque?msg=Cheque+Guardado')


@w.get('/app/ver_cheques_guardados')
@dbcontext
@auth_decorator
def list_checks():
    today = datetime.date.today()
    start, end = parse_start_end_date_with_default(
        request.query, today,
        today - datetime.timedelta(hours=12))
    result = paymentapi.list_checks(paymentdate=(start, end))
    temp = jinja_env.get_template('invoice/list_cheque.html')
    return temp.render(start=start, end=end, checks=result,
                       title='Cheques Guardados',
                       accounts=paymentapi.get_all_accounts(),
                       thisurl=request.url)


@w.get('/app/ver_cheques_para_depositar')
@dbcontext
@auth_decorator
def list_checks_deposit():
    today = datetime.date.today()
    start, end = parse_start_end_date_with_default(
        request.query, today, today)
    if start.isoweekday() == 1:
        start = start - datetime.timedelta(days=2)
    result = paymentapi.list_checks(checkdate=(start, end))
    temp = jinja_env.get_template('invoice/list_cheque.html')
    return temp.render(start=start, end=end, checks=result,
                       title='Cheques para depositar',
                       accounts=paymentapi.get_all_accounts(),
                       thisurl=request.url)


@w.get('/app/ver_cheques_por_titular')
@dbcontext
@auth_decorator
def ver_cheques_por_titular():
    start, end = parse_start_end_date_with_default(request.query, None, None)
    titular = request.query.titular
    if titular:
        result = sessionmanager.session.query(NCheck).filter(
            NCheck.holder.contains(titular))
        if start is not None:
            result = result.filter(NCheck.checkdate >= start)
        if end is not None:
            result = result.filter(NCheck.checkdate <= end)
        result = map(Check.from_db_instance, result)
    else:
        result = []
    temp = jinja_env.get_template('invoice/list_cheque.html')
    return temp.render(start=start, end=end, checks=result,
                       title='Cheques para depositar',
                       accounts=paymentapi.get_all_accounts(),
                       thisurl=request.url,
                       show_titular=True, titular=titular)


@w.post('/app/guardar_deposito')
@dbcontext
@auth_decorator
def post_guardar_deposito():
    deposit = parse_payment_from_request(request.forms, Deposit, '/app/guardar_deposito')
    paymentapi.save_payment(deposit, PaymentFormat.DEPOSIT)
    redirect('/app/guardar_deposito?msg=Deposito+Guardado')


@w.get('/app/guardar_abono')
@dbcontext
@auth_decorator
def guardar_abono():
    msg = request.query.msg
    temp = jinja_env.get_template('invoice/save_abono_form.html')
    return temp.render(stores=prodapi.get_stores(),
                       action='/app/guardar_abono',
                       msg=msg, payment_type=PaymentFormat.CASH)


@w.get('/app/guardar_retension')
@dbcontext
@auth_decorator
def guardar_retension():
    msg = request.query.msg
    temp = jinja_env.get_template('invoice/save_abono_form.html')
    return temp.render(stores=prodapi.get_stores(),
                       action='/app/guardar_abono',
                       msg=msg, payment_type='retension')


@w.post('/app/guardar_abono')
@dbcontext
@auth_decorator
def post_guardar_abono():
    payment = Payment()
    url = '/app/guardar_abono'
    payment_type = request.forms.payment_type
    if payment_type != PaymentFormat.CASH:
        url = '/app/guardar_retension'
    payment.note_id, payment.client_id = extract_nota_and_client(request.forms, url)
    payment.value = int(Decimal(request.forms.value) * 100)
    payment.date = datetime.date.today()
    paymentapi.save_payment(payment, payment_type)
    url = '/app/guardar_abono?msg=Abono+Guardado'
    if payment_type != PaymentFormat.CASH:
        url = '/app/guardar_retension?msg=Retension+Guardado'
    redirect(url)


@w.get('/app/guardar_gastos')
@w.get('/app/guardar_gastos/<uid>')
@dbcontext
@auth_decorator
def save_spent(msg='', uid=-1):
    spent = None
    if uid >= 0:
        spent = sessionmanager.session.query(NSpent).filter_by(uid=uid).first()
        if spent is None:
            msg = 'Gasto no encontrado'
    temp = jinja_env.get_template('invoice/guardar_gastos.html')
    return temp.render(msg=msg, spent=spent)


@w.post('/app/guardar_gastos')
@dbcontext
@auth_decorator
def post_save_spent():
    uid = request.forms.get('uid')
    spent = None
    create = True
    if uid is not None:
        spent = sessionmanager.session.query(NSpent).filter_by(uid=uid).first()
        create = False
        if spent is None:
            redirect('/app/guardar_gastos/{}'.format(uid))
    if spent is None:
        spent = NSpent()
    for x in ('seller', 'seller_ruc', 'invnumber',
              'invdate', 'desc', 'total', 'tax', 'retension',
              'paid_from_cashier', 'inputdate'):
        setattr(spent, x, request.forms.get(x))
    spent.total = int(Decimal(spent.total) * 100)
    spent.tax = int(Decimal(spent.tax) * 100)
    spent.retension = int(Decimal(spent.retension) * 100)
    spent.paid_from_cashier = int(Decimal(spent.paid_from_cashier) * 100)
    
    spent.invdate = parse_iso(spent.invdate)
    spent.inputdate = parse_iso(spent.inputdate)

    if create:
        sessionmanager.session.add(spent)
    sessionmanager.session.commit()
    return save_spent('Gasto Guardado')


@w.get('/app/ver_gastos')
@dbcontext
@auth_decorator
def ver_gastos():
    today = datetime.datetime.today()
    start, end = parse_start_end_date_with_default(
        request.query, today, today)

    all_spent = sessionmanager.session.query(NSpent).filter(
        NSpent.inputdate >= start,
        NSpent.inputdate <= end + datetime.timedelta(days=1))

    temp = jinja_env.get_template('invoice/ver_gastos.html')
    return temp.render(start=start, end=end, all_spent=all_spent)
