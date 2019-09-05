from collections import defaultdict
from decimal import Decimal
import json
import datetime
from operator import attrgetter
import os
import uuid

from bottle import request, redirect, static_file, Bottle, response, abort
from sqlalchemy import func

from henry import constants
from henry import hack
from henry.base.auth import get_user
from henry.base.common import parse_iso, parse_start_end_date, parse_start_end_date_with_default
from henry.base.serialization import json_dumps
from henry.base.dbapi_rest import bind_dbapi_rest
from henry.dao.document import Status
from henry.invoice.dao import PaymentFormat, InvMetadata
from henry.misc import fix_id
from henry.product.dao import Store
from henry.invoice.coreschema import NNota
from .acct_schema import ObjType, NComment, NPayment
from henry.users.dao import User
from .reports import (generate_daily_report, split_records_binary, get_transactions, payment_report,
                      get_notas_with_clients, split_records, get_turned_in_cash, get_sale_report)
from .acct_schema import NCheck, NSpent, NAccountStat
from .dao import (Todo, Check, Deposit, Payment, Bank,
                  DepositAccount, AccountStat, Spent, AccountTransaction, Comment)


def extract_nota_and_client(dbapi, form, redirect_url):
    codigo = form.get('codigo')
    almacen = form.get('almacen_id')
    if codigo:
        nota = dbapi.db_session.query(NNota).filter_by(
            codigo=codigo, almacen_id=almacen).first()
        if nota is None:
            redirect('{}?msg=Orden+Despacho+No+{}+no+existe'.format(
                redirect_url, codigo))
        return nota.id, nota.client_id
    return None, None


def make_wsgi_api(dbapi, invapi, dbcontext, auth_decorator, paymentapi, imgserver, override_transaction_getter=None):
    w = Bottle()

    @w.get('/app/api/sales')
    @dbcontext
    def get_sales():
        """ start=<start>&end=<end>
        """
        start_date, end_date = parse_start_end_date(request.query)
        if not end_date:
            end_date = datetime.date.today()
        end_date = end_date + datetime.timedelta(hours=23)
        query = dbapi.db_session.query(
            NNota.almacen_id, func.sum(NNota.total)).filter(
            NNota.timestamp >= start_date).filter(
            NNota.timestamp <= end_date).filter(
            NNota.status != Status.DELETED).group_by(NNota.almacen_id)
        result = []
        for aid, total in query:
            result.append((aid, Decimal(total) / 100))
        return json_dumps({'result': result})

    @w.get('/app/api/payment')
    @dbcontext
    def get_all_payments():
        start, end = parse_start_end_date(request.query)
        result = list(paymentapi.list_payments(start, end))
        return json_dumps({'result': result})

    @w.get('/app/api/gasto')
    @dbcontext
    def get_all_gastos():
        day = parse_iso(request.query.get('date'))
        result = dbapi.search(Spent, inputdate=day)
        return json_dumps(result)

    @w.get('/app/api/account_transaction')
    @dbcontext
    def get_account_transactions_mult_days():
        start, end = parse_start_end_date(request.query)
        # FIXME: remove this hack
        if override_transaction_getter:
            result = override_transaction_getter(start, end)
        else:
            result = get_transactions(dbapi, paymentapi, invapi, imgserver, start, end)
        return json_dumps(result)

    @w.get('/app/api/check')
    @dbcontext
    def get_checks():
        save_date = request.query.get('save_date')
        save_date_end = request.query.get('save_date_end')
        deposit_date = request.query.get('deposit_date')
        deposit_date_end = request.query.get('deposit_date_end')
        if save_date:
            save_date = (save_date, save_date_end)
        if deposit_date:
            deposit_date = (deposit_date, deposit_date_end)
        checks = paymentapi.list_checks(save_date, deposit_date)
        for x in checks:
            x.imgdeposit = imgserver.get_url_path(x.imgdeposit)
            x.imgcheck = imgserver.get_url_path(x.imgcheck)
            x.value = Decimal(x.value) / 100
        return json_dumps({'result': checks})

    @w.post('/app/api/acct_transaction')
    @dbcontext
    def post_acct_transaction():
        data = request.body.read()
        acct = AccountTransaction.deserialize(json.loads(data))
        acct.input_timestamp = datetime.datetime.now()
        acct.deleted = False
        pkey = dbapi.create(acct)
        return {'pkey': pkey}

    @w.put('/app/api/acct_transaction/<uid>')
    @dbcontext
    def put_acct_transaction(uid):
        data = json.loads(request.body.read())
        acct = AccountTransaction(uid=uid)
        count = dbapi.update(acct, data)
        return {'updated': count}

    @w.get('/app/api/noncash_sales_with_payments')
    @dbcontext
    @auth_decorator(0)
    def ver_ventas_no_efectivos():
        start, end = parse_start_end_date(request.query)
        end += datetime.timedelta(hours=23)
        sales = dbapi.db_session.query(NNota).filter(
            NNota.timestamp >= start).filter(NNota.timestamp <= end).filter(
            NNota.payment_format != PaymentFormat.CASH)

        sales = map(InvMetadata.from_db_instance, sales)
        payments = list(paymentapi.list_payments(start, end))

        result = {}
        for x in sales:
            if x.client.codigo not in result:
                result[x.client.codigo] = {}
                result[x.client.codigo]['sales'] = []
                result[x.client.codigo]['payments'] = []
            result[x.client.codigo]['sales'].append(x)

        unused_payments = []
        for x in payments:
            if x.client_id in result:
                result[x.client_id]['payments'].append(x)
            else:
                unused_payments.append(x)

        result['unused_payments'] = unused_payments
        return json_dumps({
            'unused_payments': unused_payments,
            'sales': result.items()
        })

    @w.get('/app/api/account_deposit_with_img')
    @dbcontext
    @auth_decorator(0)
    def get_account_deposit_with_img():
        today = datetime.datetime.today()
        thisyear = today - datetime.timedelta(days=365)
        turned_in = sorted(get_turned_in_cash(dbapi, thisyear, today, imgserver),
                           key=lambda x: x.date, reverse=True)
        result = defaultdict(list)
        for x in turned_in:
            if getattr(x, 'img', None):
                if len(result['with_deposit']) < 10:
                    result['with_deposit'].append(x)
            else:
                result['without_deposit'].append(x)
        return json_dumps(result)


    # account stat
    bind_dbapi_rest('/app/api/account_stat', dbapi, AccountStat, w)
    bind_dbapi_rest('/app/api/bank_account', dbapi, DepositAccount, w)
    bind_dbapi_rest('/app/api/account_deposit', dbapi, AccountTransaction, w)

    bind_dbapi_rest('/app/api/spent', dbapi, Spent, w, skips_method=('DELETE', ))

    @w.get('/app/api/pago/<uid>')
    @dbcontext
    def get_pago_with_id(uid):
        elm = dbapi.db_session.query(NPayment).filter_by(uid=uid).first()
        if elm is None:
            response.status = 404
            return ''
        return json_dumps(Payment().merge_from(elm).serialize())

    @w.delete('/app/api/pago/<uid>')
    @dbcontext
    def mark_pago_deleted(uid):
        success = dbapi.db_session.query(NPayment).filter_by(uid=uid).update({'deleted': True})
        dbapi.db_session.commit()
        return {'success': success > 0}

    @w.put('/app/api/pago/<uid>')
    @dbcontext
    def modify_payment(uid):
        data = json.loads(request.body.read())
        success = dbapi.db_session.query(NPayment).filter_by(uid=uid).update(data)
        dbapi.db_session.commit()
        return {'success': success > 0}

    @w.delete('/app/api/spent/<uid>')
    @dbcontext
    def mark_pago_deleted(uid):
        spent = Spent(uid=uid)
        sucess = dbapi.update(spent, {'deleted': True})
        dbapi.db_session.commit()
        return {'success': sucess > 0}

    @w.post('/app/api/comment')
    @dbcontext
    @auth_decorator(0)
    def post_comment():
        comment = json.loads(request.body.read())
        c = Comment()
        c.objid = comment['objid']
        c.objtype = comment['objtype']
        c.user_id = get_user(request)['username']
        c.timestamp = datetime.datetime.now()
        c.comment = comment['comment']
        dbapi.create(c)
        dbapi.db_session.commit()
        return {'comment': c.uid}

    @w.get('/app/api/sale_report_monthly')
    @dbcontext
    def sale_report_monthly():
        start, end = parse_start_end_date(request.query)
        report = get_sale_report(invapi, start, end)
        return json_dumps(report)

    return w


def make_wsgi_app(dbcontext, imgserver,
                  dbapi, paymentapi, jinja_env, auth_decorator, imagefiles, invapi):
    w = Bottle()

    @w.get('/app/resumen_form')
    @dbcontext
    @auth_decorator(1)
    def resume_form():
        temp = jinja_env.get_template('invoice/resumen_form.html')
        stores = dbapi.search(Store)
        users = dbapi.search(User)
        return temp.render(almacenes=stores, users=users)

    @w.get('/app/resumen')
    @dbcontext
    @auth_decorator(1)
    def get_resumen():
        user = request.query.get('user')
        store = request.query.get('almacen_id')
        start, end = parse_start_end_date(request.query)

        if user is None or store is None:
            abort(400, 'Escoje usuario y almacen')
        if start is None or end is None:
            abort(400, 'Hay que ingresar las fechas')

        store = int(store)
        report = payment_report(dbapi, end, start, store)

        temp = jinja_env.get_template('invoice/resumen_nuevo.html')
        return temp.render(
            start=start,
            end=end,
            user=user,
            store=dbapi.search(Store),
            report=report)

    @w.get('/app/resumen_viejo')
    @dbcontext
    @auth_decorator(1)
    def get_resumen_viejo():
        user = request.query.get('user')
        store = request.query.get('almacen_id')
        start, end = parse_start_end_date(request.query)

        if user is None or store is None:
            abort(400, 'Escoje usuario y almacen')
        if start is None or end is None:
            abort(400, 'Hay que ingresar las fechas')

        store = int(store)
        result = get_notas_with_clients(dbapi.session, end, start, store)

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
            store=dbapi.search(Store),
            ventas=ventas,
            gtotal=gtotal,
            eliminados=deleted)

    @w.get('/app/entregar_cuenta_form')
    @dbcontext
    @auth_decorator(1)
    def entrega_de_cuenta():
        temp = jinja_env.get_template('invoice/entregar_cuenta_form.html')
        return temp.render()

    @w.get('/app/crear_entrega_de_cuenta')
    @dbcontext
    @auth_decorator(1)
    def crear_entrega_de_cuenta():
        date = request.query.get('fecha')
        if date:
            date = parse_iso(date).date()
        else:
            date = datetime.date.today()
        report = generate_daily_report(dbapi, date)
        total_spent = sum((x.paid_from_cashier for x in report.spent))
        checkimgs = {check.payment_id: os.path.split(check.imgcheck)[1]
                     for check in report.checks if check.imgcheck}
        existing = dbapi.get(date, AccountStat)
        all_img = list(imgserver.getimg(objtype='entrega_cuenta', objid=date.isoformat()))
        temp = jinja_env.get_template('invoice/crear_entregar_cuenta_form.html')
        total_cash = sum(report.cash.values()) + report.other_cash
        return temp.render(
            cash=report.cash, others=report.other_by_client,
            total_cash=total_cash,
            deleted=report.deleted,
            date=date.isoformat(),
            pagos=report.payments,
            all_spent=report.spent,
            total_spent=total_spent,
            retension=report.retension,
            other_cash=report.other_cash,
            imgs=all_img,
            checkimgs=checkimgs,
            existing=existing)

    def get_cents_with_default(number, default=0):
        try:
            return int(float(number) * 100)
        except ValueError:
            return default

    @w.post('/app/crear_entrega_de_cuenta')
    @dbcontext
    @auth_decorator(0)
    def post_crear_entrega_de_cuenta():
        cash = request.forms.get('cash', 0)
        gastos = request.forms.get('gastos', 0)
        deposito = request.forms.get('deposito', 0)
        turned_cash = request.forms.get('valor', 0)
        diff = request.forms.get('diff', 0)
        date = request.forms.get('date')

        cash = get_cents_with_default(cash)
        gastos = get_cents_with_default(gastos)
        deposito = get_cents_with_default(deposito)
        turned_cash = get_cents_with_default(turned_cash)
        diff = get_cents_with_default(diff)
        date = parse_iso(date).date()

        userid = get_user(request)['username']
        if request.forms.get('submit') == 'Crear':
            stat = AccountStat(
                date=date,
                total_spend=gastos,
                turned_cash=turned_cash,
                deposit=deposito,
                created_by=userid
            )
            dbapi.create(stat)
            dbapi.db_session.flush()
        else:
            dbapi.update(AccountStat(date=date),
                         {'revised_by': userid, 'turned_cash': turned_cash,
                          'deposit': deposito, 'diff': diff})

        redirect('/app/crear_entrega_de_cuenta?fecha={}'.format(date.isoformat()))

    @w.get('/app/entrega_de_cuenta_list')
    @dbcontext
    @auth_decorator(0)
    def ver_entrega_de_cuenta_list():
        start, end = parse_start_end_date(request.query)
        if end is None:
            end = datetime.date.today()
        if start is None:
            start = datetime.date.today() - datetime.timedelta(days=7)

        accts = dbapi.db_session.query(NAccountStat).filter(
            NAccountStat.date >= start, NAccountStat.date <= end)
        temp = jinja_env.get_template('invoice/entrega_de_cuenta_list.html')
        return temp.render(accts=accts, start=start, end=end)

    def render_form_with_msg(path, title):
        msg = request.query.msg
        temp = jinja_env.get_template(path)
        return temp.render(msg=msg, title=title)

    @w.get('/app/crear_cuenta_form')
    @dbcontext
    @auth_decorator(0)
    def create_cuenta():
        return render_form_with_msg(
            'invoice/crear_banco_form.html', title='Crear Cuenta')

    @w.get('/app/crear_banco_form')
    @dbcontext
    @auth_decorator(0)
    def create_bank():
        return render_form_with_msg(
            'invoice/crear_banco_form.html', title='Crear Banco')

    @w.post('/app/crear_banco_form')
    @dbcontext
    @auth_decorator(0)
    def post_create_bank():
        name = request.forms.name
        bank = Bank(nombre=name)
        dbapi.create(bank)
        redirect('/app/crear_banco_form?msg=Cuenta+Creada')

    @w.post('/app/crear_cuenta_form')
    @dbcontext
    @auth_decorator(0)
    def post_create_cuenta():
        name = request.forms.name
        acc = DepositAccount(nombre=name)
        dbapi.create(acc)
        redirect('/app/crear_banco_form?msg=Cuenta+Creada')

    @w.post('/app/guardar_cheque_deposito')
    @dbcontext
    @auth_decorator(0)
    def post_guardar_cheque_deposito():
        nexturl = request.forms.get('next', '/app')
        for key, value in request.forms.items():
            print key, value
            if key.startswith('acct-'):
                key = key.replace('acct-', '')
                print key, value
                dbapi.db_session.query(NCheck).filter_by(uid=key).update(
                    {NCheck.deposit_account: value})
                dbapi.db_session.flush()
        redirect(nexturl)

    @w.get('/app/ver_cheque/<cid>')
    @dbcontext
    @auth_decorator(0)
    def ver_cheque(cid):
        check = paymentapi.get_check(cid)
        if check.imgcheck:
            _, check.imgcheck = os.path.split(check.imgcheck)
        if check.imgdeposit:
            _, check.imgdeposit = os.path.split(check.imgdeposit)
        temp = jinja_env.get_template('invoice/ver_cheque.html')
        comments = list(dbapi.db_session.query(NComment).filter_by(
            objtype=ObjType.CHECK, objid=str(cid)))
        return temp.render(check=check, comments=comments)

    @w.post('/app/postregar_cheque')
    @dbcontext
    @auth_decorator(0)
    def postregar_cheque():
        checkid = request.forms.checkid
        new_date = parse_iso(request.forms.new_date).date()
        session = dbapi.db_session
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
    @auth_decorator(0)
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
        dbapi.db_session.query(NCheck).filter_by(
            uid=cid).update({row: filename, NCheck.status: newstatus})
        redirect('/app/ver_cheque/{}'.format(cid))

    save_check_image.image = None

    @w.get('/app/imgcheck/<cid>')
    @dbcontext
    @auth_decorator(0)
    def check_image_get(cid):
        check = paymentapi.get(cid)
        return static_file(check.imgcheck, root='.')

    @w.get('/app/guardar_deposito')
    @dbcontext
    @auth_decorator(0)
    def guardar_deposito():
        msg = request.query.msg
        temp = jinja_env.get_template('invoice/save_deposito_form.html')
        return temp.render(cuentas=dbapi.search(DepositAccount),
                           stores=dbapi.search(Store),
                           msg=msg)

    @w.get('/app/guardar_cheque')
    @dbcontext
    @auth_decorator(0)
    def save_check_form():
        msg = request.query.msg
        temp = jinja_env.get_template('invoice/save_check_form.html')
        return temp.render(banks=dbapi.search(Bank),
                           stores=dbapi.search(Store),
                           msg=msg)

    def parse_payment_from_request(form, clazz, url):
        date = datetime.date.today()
        if request.forms.ingresado == 'ayer':
            date = date - datetime.timedelta(days=1)
        payment = clazz.deserialize(request.forms)
        payment.note_id, payment.client_id = extract_nota_and_client(dbapi, form, url)
        payment.value = int(Decimal(payment.value) * 100)
        payment.date = date
        return payment

    @w.post('/app/guardar_cheque')
    @dbcontext
    @auth_decorator(0)
    def save_check():
        check = parse_payment_from_request(
            request.forms, Check, '/app/guardar_cheque')
        check.checkdate = parse_iso(check.checkdate)
        paymentapi.save_check(check)
        redirect('/app/guardar_cheque?msg=Cheque+Guardado')

    @w.get('/app/ver_cheques_guardados')
    @dbcontext
    @auth_decorator(0)
    def list_checks():
        today = datetime.date.today()
        start, end = parse_start_end_date_with_default(
            request.query, today,
            today - datetime.timedelta(hours=12))
        result = paymentapi.list_checks(paymentdate=(start, end))
        temp = jinja_env.get_template('invoice/list_cheque.html')
        return temp.render(start=start, end=end, checks=result,
                           title='Cheques Guardados',
                           accounts=dbapi.search(DepositAccount),
                           thisurl=request.url)

    @w.get('/app/ver_cheques_para_depositar')
    @dbcontext
    @auth_decorator(0)
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
                           accounts=dbapi.search(Store),
                           thisurl=request.url)

    @w.get('/app/ver_cheques_por_titular')
    @dbcontext
    @auth_decorator(0)
    def ver_cheques_por_titular():
        start, end = parse_start_end_date_with_default(request.query, None, None)
        titular = request.query.titular
        if titular:
            result = dbapi.db_session.query(NCheck).filter(
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
                           accounts=dbapi.search(DepositAccount),
                           thisurl=request.url,
                           show_titular=True, titular=titular)

    @w.post('/app/guardar_deposito')
    @dbcontext
    @auth_decorator(0)
    def post_guardar_deposito():
        deposit = parse_payment_from_request(
            request.forms, Deposit, '/app/guardar_deposito')
        paymentapi.save_payment(deposit, PaymentFormat.DEPOSIT)
        redirect('/app/guardar_deposito?msg=Deposito+Guardado')

    @w.get('/app/guardar_abono')
    @dbcontext
    @auth_decorator(0)
    def guardar_abono():
        msg = request.query.msg
        temp = jinja_env.get_template('invoice/save_abono_form.html')
        return temp.render(stores=dbapi.search(Store),
                           action='/app/guardar_abono',
                           msg=msg, payment_type=PaymentFormat.CASH)

    @w.get('/app/guardar_retension')
    @dbcontext
    @auth_decorator(0)
    def guardar_retension():
        msg = request.query.msg
        temp = jinja_env.get_template('invoice/save_abono_form.html')
        return temp.render(stores=dbapi.search(Store),
                           action='/app/guardar_abono',
                           msg=msg, payment_type='retension')

    @w.post('/app/guardar_abono')
    @dbcontext
    @auth_decorator(0)
    def post_guardar_abono():
        payment = Payment()
        url = '/app/guardar_abono'
        payment_type = request.forms.payment_type
        if payment_type != PaymentFormat.CASH:
            url = '/app/guardar_retension'
        payment.note_id, payment.client_id = extract_nota_and_client(
            dbapi, request.forms, url)
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
    @auth_decorator(0)
    def save_spent(msg='', uid=-1):
        spent = None
        if uid >= 0:
            spent = dbapi.db_session.query(NSpent).filter_by(uid=uid).first()
            if spent is None:
                msg = 'Gasto no encontrado'
        temp = jinja_env.get_template('invoice/guardar_gastos.html')
        return temp.render(msg=msg, spent=spent)

    @w.post('/app/guardar_gastos')
    @dbcontext
    @auth_decorator(0)
    def post_save_spent():
        uid = request.forms.get('uid')
        spent = None
        create = True
        if uid is not None:
            spent = dbapi.db_session.query(NSpent).filter_by(uid=uid).first()
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
            dbapi.db_session.add(spent)
        dbapi.db_session.commit()
        return save_spent('Gasto Guardado')

    @w.get('/app/ver_gastos')
    @dbcontext
    @auth_decorator(0)
    def ver_gastos():
        today = datetime.datetime.today()
        start, end = parse_start_end_date_with_default(
            request.query, today, today)

        all_spent = dbapi.db_session.query(NSpent).filter(
            NSpent.inputdate >= start,
            NSpent.inputdate <= end + datetime.timedelta(days=1))

        temp = jinja_env.get_template('invoice/ver_gastos.html')
        return temp.render(start=start, end=end, all_spent=all_spent)

    class CustomerSell(object):
        def __init__(self):
            self.subtotal = 0
            self.iva = 0
            self.count = 0
            self.total = 0

    def group_by_customer(inv):
        result = defaultdict(CustomerSell)
        for i in inv:
            if i.client.codigo is None:
                i.client.codigo = 'NA'
            cliente_id = fix_id(i.client.codigo)
            if not i.discount:
                i.discount = 0
            if not i.tax:
                i.tax = 0
            result[cliente_id].subtotal += (i.subtotal - i.discount)
            result[cliente_id].iva += i.tax
            result[cliente_id].total += i.total
            result[cliente_id].count += 1
        return result

    @w.get('/app/accounting_form')
    @dbcontext
    def get_sells_xml_form():
        temp = jinja_env.get_template('accounting/ats_form.html')
        stores = filter(lambda x: x.ruc, dbapi.search(Store))
        return temp.render(stores=stores, title='ATS')

    class Meta(object):
        pass

    @w.get('/app/accounting.xml')
    @dbcontext
    def get_sells_xml():
        start_date, end_date = parse_start_end_date(request.query)
        end_date = end_date + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
        form_type = request.query.get('form_type')

        ruc = request.query.get('alm')
        invs = list(invapi.search_metadata_by_date_range(
            start_date, end_date, other_filters={'almacen_ruc': ruc}))
        for inv in invs:
            inv.client.codigo = hack.fix_id_error(inv.client.codigo)
        deleted, sold = split_records_binary(invs, lambda x: x.status == Status.DELETED)
        grouped = group_by_customer(sold)

        meta = Meta()
        meta.date = start_date
        meta.total = reduce(lambda acc, x: acc + x.subtotal, grouped.values(), 0)
        meta.almacen_ruc = ruc
        meta.almacen_name = [x.nombre for x in dbapi.search(Store) if x.ruc == ruc][0]
        temp = jinja_env.get_template('accounting/resumen_agrupado.html')
        if form_type == 'ats':
            temp = jinja_env.get_template('accounting/ats.xml')
            response.set_header('Content-disposition', 'attachment')
            response.set_header('Content-type', 'application/xml')
        return temp.render(vendidos=grouped, eliminados=deleted, meta=meta)

    @w.get('/app/img/<rest:path>')
    @dbcontext
    @auth_decorator(0)
    def img(rest):
        if constants.ENV == 'test':
            return static_file(rest, root=constants.IMAGE_PATH)
        else:
            response.set_header('X-Accel-Redirect', '/image/{}'.format(rest))
            response.set_header('Content-Type', '')

    def save_img_from_request(therequest):
        imgdata = therequest.files.get('img')
        objtype = therequest.forms.get('objtype')
        objid = therequest.forms.get('objid')
        do_replace = therequest.forms.get('replace')
        return imgserver.saveimg(objtype, objid, imgdata, do_replace)

    @w.post('/app/attachimg')
    @dbcontext
    @auth_decorator(0)
    def post_img():
        redirect_url = request.forms.get('redirect_url')
        save_img_from_request(request)
        redirect(redirect_url)

    @w.post('/app/api/attachimg')
    @dbcontext
    @auth_decorator(0)
    def post_img():
        img = save_img_from_request(request)
        url = imgserver.get_url_path(img.path)
        return {'url': url}

    @w.get('/app/api/comment')
    @dbcontext
    def view_comments():
        temp = jinja_env.get_template('comments.html')
        all_comments = dbapi.search(Comment)
        all_comments = sorted(all_comments, key=attrgetter('timestamp'), reverse=True)
        return temp.render(comments=all_comments)

    @w.get('/app/sale_report_monthly')
    @dbcontext
    def sale_report_monthly():
        start, end = parse_start_end_date(request.query)
        report = get_sale_report(invapi, start, end)
        report.best_sellers = sorted(report.best_sellers, key=lambda x: x[1].value, reverse=True)
        temp = jinja_env.get_template('sale_report_monthly.html')
        return temp.render(report=report)

    return w
