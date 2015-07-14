from collections import defaultdict
from datetime import timedelta
from operator import attrgetter
from henry.base.schema import NNota, NCliente
from henry.config import prodapi
from henry.dao import InvMetadata, Status


def get_notas_with_clients(session, end_date, start_date, store=None, user_id=None):
    end_date = end_date + timedelta(days=1) - timedelta(seconds=1)

    def decode_db_row_with_client(db_raw):
        m = InvMetadata.from_db_instance(db_raw[0])
        m.client.nombres = db_raw.nombres
        m.client.apellidos = db_raw.apellidos
        if not m.almacen_name:
            alm = prodapi.get_store_by_id(m.almacen_id)
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
    all_sale = list(get_notas_with_clients(session, start, end, store_id, user_id))
    report = Report()

    by_status = split_records(all_sale, attrgetter('status'))
    report.deleted = by_status[Status.DELETED]
    committed = by_status[Status.COMITTED]

    by_payment = split_records(committed, attrgetter('payment_format'))
    report.list_by_payment = by_payment

    def get_total(content):
        return reduce(lambda acc, x: acc + x.total, content, 0)
    report.total_by_payment = {key: get_total(value) for key, value in report.list_by_payment.items()}
    return report
