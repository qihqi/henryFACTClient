from collections import defaultdict
from datetime import timedelta
from henry.base.schema import NNota, NCliente
from henry.config import prodapi
from henry.dao import InvMetadata


def get_notas_with_clients(session, store, start_date, end_date):
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


