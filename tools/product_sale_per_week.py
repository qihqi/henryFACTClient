from henry.config import sessionmanager
from henry.layer1.schema import NItemDespacho, NOrdenDespacho
import datetime
from datetime import timedelta


def get_all_prod_ids(session, start_date, end_date):
    return session.query(NItemDespacho).join(
        NOrdenDespacho, 
        NItemDespacho.desp_cod_id==NOrdenDespacho.id).filter(
        NOrdenDespacho.fecha >= start_date).filter(
        NOrdenDespacho.fecha <= end_date)

def main():

    with sessionmanager as session:
        start_date = datetime.date(2015,01,01)
        end_date = datetime.date.today()
        current_prods = set()
        while start_date < end_date:
            next_prods = set()
            for x in get_all_prod_ids(session, 
                    start_date, start_date + timedelta(days=7)):
                next_prods.add(x.producto_id)
            print start_date.isoformat(), 'productos vendidos ', len(next_prods)
            print start_date.isoformat(), 'productos nuevos ', len(next_prods - current_prods)
            start_date += timedelta(days=7)
            current_prods = next_prods
main()
