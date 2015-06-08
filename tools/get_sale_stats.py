from datetime import date
from decimal import Decimal
from collections import defaultdict

from sqlalchemy.orm import sessionmaker 
from sqlalchemy import create_engine
from henry.base.schema import NOrdenDespacho


CONN_STRING = 'mysql+mysqldb://root:wolverineaccess@localhost/henry'
engine = create_engine(CONN_STRING)
sessionfactory = sessionmaker(bind=engine)

def get_all_sales(session, start, end, bodega_id):
    return session.query(NOrdenDespacho).filter(
            NOrdenDespacho.fecha >= start).filter(
            NOrdenDespacho.fecha <= end).filter_by(bodega_id=bodega_id)

    
def main():
    session = sessionfactory()
    all_inv = get_all_sales(session, date(2012, 01, 01), date(2015, 12, 31), 2)
    by_date = defaultdict(Decimal)
    by_week = defaultdict(Decimal)
    by_date_of_week = defaultdict(Decimal)
    by_month = defaultdict(Decimal)

    for i in all_inv:
        week_num = (i.fecha - date(2014, 01, 01)).days / 7
        day_of_week = i.fecha.weekday()
        month = i.fecha.month
        yearmonth = i.fecha.year * 100 + i.fecha.month

        by_date[i.fecha.isoformat()] += i.total
        by_week[week_num] += i.total
        by_date_of_week[day_of_week] += i.total
        by_month[yearmonth] += i.total

    #print 'by date'
    #print_dict(by_date) 
    print 'by month'
    print_dict(by_month) 
    print 'by days_of_week'
    print_dict(by_date_of_week) 
    #print 'by week num'
    #print_dict(by_week) 

    print 'avg', avg_dict(by_date), avg_dict(by_week), avg_dict(by_month)

#    plot_all(by_month)

def print_dict(d):
    for x, y in d.items():
        print x,'\t', y

def avg_dict(d):
    return sum(d.values()) / len(d)


if __name__ == '__main__':
    main()
