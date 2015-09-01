from collections import defaultdict
from datetime import timedelta
from operator import attrgetter
from decimal import Decimal
from henry.config import prodapi, transapi
from henry.schema.inv import NNota
from henry.schema.user import NCliente

from henry.coreconfig import storeapi, invapi
from henry.dao.order import InvMetadata
from henry.dao.document import Status


def get_notas_with_clients(session, end_date, start_date,
                           store=None, user_id=None):
    end_date = end_date + timedelta(days=1) - timedelta(seconds=1)

    def decode_db_row_with_client(db_raw):
        m = InvMetadata.from_db_instance(db_raw[0])
        m.client.nombres = db_raw.nombres
        m.client.apellidos = db_raw.apellidos
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
