import datetime
from collections import defaultdict
from datetime import timedelta
from operator import attrgetter
from decimal import Decimal

from sqlalchemy import func

from henry.accounting.acct_schema import NPayment, NCheck, NSpent
from henry.accounting.dao import Spent, AccountStat, AccountTransaction, Image, Payment
from henry.base.serialization import SerializableMixin
from henry.config import prodapi, transapi
from henry.product.dao import Store
from henry.invoice.coreschema import NNota
from henry.users.schema import NCliente
from henry.base.dbapi import decode_str
from henry.coreconfig import storeapi, invapi
from henry.invoice.dao import PaymentFormat, InvMetadata
from henry.dao.document import Status
from henry.users.dao import Client


def get_notas_with_clients(session, end_date, start_date,
                           store=None, user_id=None):
    end_date = end_date + timedelta(days=1) - timedelta(seconds=1)

    def decode_db_row_with_client(db_raw):
        m = InvMetadata.from_db_instance(db_raw[0])
        m.client.nombres = decode_str(db_raw.nombres)
        m.client.apellidos = decode_str(db_raw.apellidos)
        if not m.almacen_name:
            alm = storeapi.get(m.almacen_id)
            m.almacen_name = alm.nombre
        return m

    result = session.query(NNota, NCliente.nombres, NCliente.apellidos).filter(
        NNota.timestamp >= start_date).filter(
        NNota.timestamp <= end_date).filter(NCliente.codigo == NNota.client_id)
    if store is not None:
        result = result.filter_by(almacen_id=store)
    if user_id is not None:
        result = result.filter_by(user_id=user_id)
    return map(decode_db_row_with_client, result)


def split_records(source, classifier):
    result = defaultdict(list)
    for s in source:
        result[classifier(s)].append(s)
    return result


def split_records_binary(source, pred):
    result = defaultdict(list)
    for s in source:
        result[bool(pred(s))].append(s)
    return result[True], result[False]


def group_by_records(source, classifier, valuegetter):
    result = defaultdict(int)
    for s in source:
        result[classifier(s)] += valuegetter(s)
    return result


class Report(object):
    def __init__(self):
        self.total_by_payment = None
        self.list_by_payment = None
        self.deleted = None


def payment_report(session, start, end, store_id=None, user_id=None):
    """
    A report of sales given dates grouped by payment format.
    Each payment format can be printed as a single total or a list of invoices
    :return:
    """
    all_sale = list(get_notas_with_clients(
        session, start, end, store_id, user_id))
    report = Report()

    by_status = split_records(all_sale, attrgetter('status'))
    report.deleted = by_status[Status.DELETED]
    committed = by_status[Status.COMITTED]

    by_payment = split_records(committed, attrgetter('payment_format'))
    report.list_by_payment = by_payment

    def get_total(content):
        return reduce(lambda acc, x: acc + x.total, content, 0)

    report.total_by_payment = {
        key: get_total(value) for key, value in
        report.list_by_payment.items()}
    return report


class InvRecord(object):
    def __init__(self, thedate, thetype, value, status=None, comment=None):
        self.date = thedate
        self.type = thetype
        self.value = value
        self.status = status
        self.comment = comment


def bodega_reports(bodega_id, start, end):
    alms = prodapi.store.search(bodega_id=bodega_id)
    alms = set((x.almacen_id for x in alms))
    sale = invapi.search_metadata_by_date_range(start, end)
    sale = filter(lambda x: x.almacen_id in alms and x.status != Status.DELETED, sale)

    sale_by_date = group_by_records(
        source=sale,
        classifier=lambda x: x.timestamp.date(),
        valuegetter=lambda x: Decimal(x.subtotal - (x.discount if x.discount else 0)) / (-100)
    )

    records = []
    records.extend((InvRecord(d, 'SALE', i, None) for d, i in sale_by_date.items()))

    def addtrans(trans, thetype):
        in_, out = (lambda x: x.dest == bodega_id), (lambda x: x.origin == bodega_id)
        thefilter, m = ((in_, 1) if thetype == 'INGRESS' else (out, -1))
        filtered = filter(thefilter, trans)
        records.extend((InvRecord(i.timestamp.date(), thetype, m * i.value, i.status, i.uid)
                        for i in filtered))

    alltrans = list(transapi.search_metadata_by_date_range(start, end))
    addtrans(alltrans, 'INGRESS')
    addtrans(alltrans, 'EGRESS')
    records.sort(key=attrgetter('date'), reverse=True)
    return records


class DailyReport(SerializableMixin):
    def __init__(self, cash, other_by_client,
                 retension, spent, deleted_invoices, payments, checks, deleted, other_cash):
        self.cash = cash
        self.other_by_client = other_by_client
        self.retension = retension
        self.spent = spent
        self.deleted_invoices = deleted_invoices
        self.payments = payments
        self.checks = checks
        self.deleted = deleted
        self.other_cash = other_cash


def generate_daily_report(dbapi, day):
    all_sale = list(filter(attrgetter('almacen_id'),
                           get_notas_with_clients(dbapi.db_session, day, day)))

    deleted, other = split_records_binary(all_sale, lambda x: x.status == Status.DELETED)
    cashed, noncash = split_records_binary(other, lambda x: x.payment_format == PaymentFormat.CASH)
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
    all_spent = list(dbapi.db_session.query(NSpent).filter(
        NSpent.inputdate >= day, NSpent.inputdate < day + datetime.timedelta(days=1)))

    return DailyReport(
        cash=sale_by_store,
        other_by_client=noncash,
        retension=retension,
        spent=all_spent,
        deleted_invoices=deleted,
        payments=payments,
        checks=checks,
        deleted=deleted,
        other_cash=other_cash,
    )


def make_acct_trans(value):
    return AccountTransaction(
        value=Decimal(value) / 100,
        desc='Deposito/Entregado',
        type='turned_in')


def get_sales_as_transactions(dbapi, start_date, end_date):
    notas = dbapi.db_session.query(
        func.DATE(NNota.timestamp), NNota.almacen_id, func.sum(NNota.total)).filter(
        NNota.timestamp >= start_date).filter(
        NNota.timestamp <= end_date).filter(
        NNota.status != Status.DELETED).filter(
        NNota.payment_format != PaymentFormat.CREDIT).filter(
        NNota.almacen_id is not None).group_by(
        func.DATE(NNota.timestamp), NNota.almacen_id)
    all_alms = {x.almacen_id: x for x in dbapi.search(Store)}
    for x in notas:
        if x[1] is None:
            continue
        yield AccountTransaction(
            uid='sale{}.{}'.format(x[0].isoformat(), x[1]),
            date=x[0],
            value=Decimal(int(x[2])) / 100,
            desc='Venta {}: {}'.format(x[0], all_alms[x[1]].nombre),
            type='venta')


def get_payments_as_transactions(dbapi, start_date, end_date):
    payments = []
    payments_credit = []
    for pago, pformat in dbapi.db_session.query(NPayment, NNota.payment_format).join(
            NNota, NPayment.note_id == NNota.id).filter(
            NPayment.date >= start_date, NPayment.date <= end_date):
        if pago.type == PaymentFormat.CASH:
            continue  # cash payment is already accounted for
        thetype = AccountTransaction.CUSTOMER_PAYMENT
        if pago.type == PaymentFormat.DEPOSIT:
            thetype = AccountTransaction.CUSTOMER_PAYMENT_DEPOSIT
        if pago.type == PaymentFormat.CHECK:
            thetype = AccountTransaction.CUSTOMER_PAYMENT_CHECK
        acct = AccountTransaction(
            uid='pago '+str(pago.uid),
            date=pago.date,
            value=-Decimal(pago.value) / 100,
            desc='{} para Factura {}'.format(pago.type, pago.note_id),
            type=thetype)
        if pformat == PaymentFormat.CREDIT:
            payments_credit.append(acct)
        else:
            payments.append(acct)
    return payments, payments_credit


def get_spent_as_transactions(dbapi, start_date, end_date):
    for gasto in dbapi.search(Spent, **{'inputdate-gte': start_date, 'inputdate-lte': end_date}):
        if gasto.paid_from_cashier is None:
            print 'ERROR', gasto.serialize()
            continue
        yield AccountTransaction(
            uid='gasto'+str(gasto.uid),
            date=gasto.inputdate.date(),
            value=(-Decimal(gasto.paid_from_cashier) / 100),
            desc=gasto.desc,
            type='gasto')


def get_turned_in_cash(dbapi, start_date, end_date, imageserver):
    all_acct = list(dbapi.search(AccountTransaction, **{'date-gte': start_date, 'date-lte': end_date}))
    imgs = {x.objid: x for x in dbapi.search(Image, objtype='account_transaction')}
    for acct in all_acct:
        key = str(acct.uid)
        if key in imgs:
            acct.img = imageserver.get_url_path(imgs[key].path)
    return all_acct


def get_transactions(dbapi, paymentapi, invapi, imageserver, start_date, end_date):
    delta = datetime.timedelta(hours=23)
    sales = list(get_sales_as_transactions(dbapi, start_date, end_date + delta))
    spent = list(get_spent_as_transactions(dbapi, start_date, end_date))
    turned_in = list(get_turned_in_cash(dbapi, start_date, end_date, imageserver))
    payments, payments_credit = get_payments_as_transactions(dbapi, start_date, end_date)
    sales_credit = list(invapi.search_metadata_by_date_range(
        start_date, end_date + delta, Status.COMITTED,
        {'payment_format': PaymentFormat.CREDIT}))
    for x in sales_credit:
        x.client = dbapi.get(x.client.codigo, Client)
    return {
        'result': sales + spent + turned_in + payments,
        'credit': sales_credit,
        'payment_credit': payments_credit,
    }
