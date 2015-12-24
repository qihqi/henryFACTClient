import datetime
import os
from decimal import Decimal
from operator import attrgetter
import uuid

from bottle import request, redirect, static_file, Bottle

from henry.base.auth import get_user
from henry.base.common import parse_iso, parse_start_end_date, parse_start_end_date_with_default

from henry.product.dao import Store
from henry.schema.inv import NNota
from henry.dao.document import Status
from henry.dao.order import PaymentFormat

from .acct_schema import ObjType, NComment
from .reports import get_notas_with_clients, split_records, group_by_records
from .acct_schema import NPayment, NCheck, NSpent, NAccountStat
from .dao import Todo, Check, Deposit, Payment, Bank, DepositAccount, AccountStat


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


def make_wsgi_api(invapi, dbcontext, auth_decorator):
    w = Bottle()

    @w.get('/app/api/sales')
    @dbcontext
    def get_sales():
        """ start=<start>&end=<end>&almacen_id=<>&almacen_ruc=<>&group_by=''
        """
        start_date, end_date = parse_start_end_date(request.query)
        if not end_date:
            end_date = datetime.datetime.now()

        alm_id = request.query.get('almacen_id', None)
        alm_ruc = request.query.get('almacen_ruc', None)
        group_by = request.query.get('group_by', None)
        filters = {}
        if alm_id:
            filters['almacen_id'] = alm_id
        if alm_ruc:
            filters['almacen_ruc'] = alm_ruc
        items = invapi.search_metadata_by_date_range(start_date, end_date, other_filters=filters)
        items = list(items)
        total = sum(x.total for x in items)
        iva = sum(x.tax or 0 for x in items)
        count = len(items)
        result = {'total': total, 'iva': iva, 'count': count}
        if group_by:
            if group_by == 'day':
                group_func = lambda x: x.timestamp.date().isoformat()
            else:
                group_func = attrgetter(group_by)
            subgroups = group_by_records(items, group_func, attrgetter('total'))
            result['groups'] = subgroups
        return result

    return w


def make_wsgi_app(dbcontext, imgserver,
                  dbapi, paymentapi, jinja_env, auth_decorator, imagefiles):
    w = Bottle()

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

        # I don't care those without almacen id for now
        all_sale = list(filter(attrgetter('almacen_id'),
                               get_notas_with_clients(dbapi.db_session, date, date)))
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
        query = dbapi.db_session.query(NPayment).filter(NPayment.note_id.in_(ids))

        # only retension for cash invoices need to be accounted separately.
        by_retension = split_records(query, lambda x: x.type == 'retension' and x.note_id in cashids)
        other_cash = sum((x.value for x in by_retension[False] if x.type == PaymentFormat.CASH))
        total_cash = sum(sale_by_store.values()) + other_cash
        payments = split_records(by_retension[False], attrgetter('client_id'))
        retension = by_retension[True]
        check_ids = [x.uid for x in by_retension[False] if x.type == PaymentFormat.CHECK]
        checks = dbapi.db_session.query(NCheck).filter(NCheck.payment_id.in_(check_ids))
        checkimgs = {check.payment_id: os.path.split(check.imgcheck)[1] for check in checks if check.imgcheck}

        all_spent = list(dbapi.db_session.query(NSpent).filter(
            NSpent.inputdate >= date, NSpent.inputdate < date + datetime.timedelta(days=1)))
        total_spent = sum((x.paid_from_cashier for x in all_spent))

        existing = dbapi.get(date, AccountStat)
        all_img = list(imgserver.getimg(objtype='entrega_cuenta', objid=date.isoformat()))
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
            imgs=all_img,
            checkimgs=checkimgs,
            existing=existing)

    @w.post('/app/crear_entrega_de_cuenta')
    @dbcontext
    @auth_decorator
    def post_crear_entrega_de_cuenta():
        cash = request.forms.get('cash', 0)
        gastos = request.forms.get('gastos', 0)
        deposito = request.forms.get('deposito', 0)
        turned_cash = request.forms.get('valor', 0)
        diff = request.forms.get('diff', 0)
        date = request.forms.get('date')

        cash = int(float(cash) * 100)
        gastos = int(float(gastos) * 100)
        deposito = int(float(deposito) * 100)
        turned_cash = int(float(turned_cash) * 100)
        date = parse_iso(date).date()
        diff = int(float(diff) * 100)

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
            now = datetime.datetime.now()
            todo1 = Todo(objtype=ObjType.ACCOUNT, objid=date, status='PENDING',
                         msg='Papeleta de deposito de {}: ${}'.format(date, Decimal(deposito) / 100),
                         creation_date=now, due_date=now)
            todo2 = Todo(objtype=ObjType.ACCOUNT, objid=date, status='PENDING',
                         msg='Papeleta de deposito de {}: ${}'.format(date, Decimal(turned_cash) / 100),
                         creation_date=now, due_date=now)
            dbapi.create(todo1)
            dbapi.create(todo2)

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
        bank = Bank(nombre=name)
        dbapi.create(bank)
        redirect('/app/crear_banco_form?msg=Cuenta+Creada')

    @w.post('/app/crear_cuenta_form')
    @dbcontext
    @auth_decorator
    def post_create_cuenta():
        name = request.forms.name
        acc = DepositAccount(nombre=name)
        dbapi.create(acc)
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
                dbapi.db_session.query(NCheck).filter_by(uid=key).update(
                    {NCheck.deposit_account: value})
                dbapi.db_session.flush()
        redirect(nexturl)

    @w.get('/app/ver_cheque/<cid>')
    @dbcontext
    @auth_decorator
    def ver_cheque(cid):
        check = dbapi.get(cid, Check)
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
    @auth_decorator
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
        dbapi.db_session.query(NCheck).filter_by(
            uid=cid).update({row: filename, NCheck.status: newstatus})
        redirect('/app/ver_cheque/{}'.format(cid))

    save_check_image.image = None

    @w.get('/app/imgcheck/<cid>')
    @dbcontext
    @auth_decorator
    def check_image_get(cid):
        check = dbapi.get(cid, Check)
        return static_file(check.imgcheck, root='.')

    @w.get('/app/guardar_deposito')
    @dbcontext
    @auth_decorator
    def guardar_deposito():
        msg = request.query.msg
        temp = jinja_env.get_template('invoice/save_deposito_form.html')
        return temp.render(cuentas=dbapi.search(DepositAccount),
                           stores=dbapi.search(Store),
                           msg=msg)


    @w.get('/app/guardar_cheque')
    @dbcontext
    @auth_decorator
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
    @auth_decorator
    def save_check():
        check = parse_payment_from_request(
            request.forms, Check, '/app/guardar_cheque')
        check.checkdate = parse_iso(check.checkdate)
        dbapi.create(check)
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
                           accounts=dbapi.search(Store),
                           thisurl=request.url)

    @w.get('/app/ver_cheques_por_titular')
    @dbcontext
    @auth_decorator
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
    @auth_decorator
    def post_guardar_deposito():
        deposit = parse_payment_from_request(
            request.forms, Deposit, '/app/guardar_deposito')
        paymentapi.save_payment(deposit, PaymentFormat.DEPOSIT)
        redirect('/app/guardar_deposito?msg=Deposito+Guardado')

    @w.get('/app/guardar_abono')
    @dbcontext
    @auth_decorator
    def guardar_abono():
        msg = request.query.msg
        temp = jinja_env.get_template('invoice/save_abono_form.html')
        return temp.render(stores=dbapi.search(Store),
                           action='/app/guardar_abono',
                           msg=msg, payment_type=PaymentFormat.CASH)

    @w.get('/app/guardar_retension')
    @dbcontext
    @auth_decorator
    def guardar_retension():
        msg = request.query.msg
        temp = jinja_env.get_template('invoice/save_abono_form.html')
        return temp.render(stores=dbapi.search(Store),
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
    @auth_decorator
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
    @auth_decorator
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
    @auth_decorator
    def ver_gastos():
        today = datetime.datetime.today()
        start, end = parse_start_end_date_with_default(
            request.query, today, today)

        all_spent = dbapi.db_session.query(NSpent).filter(
            NSpent.inputdate >= start,
            NSpent.inputdate <= end + datetime.timedelta(days=1))

        temp = jinja_env.get_template('invoice/ver_gastos.html')
        return temp.render(start=start, end=end, all_spent=all_spent)

    return w
