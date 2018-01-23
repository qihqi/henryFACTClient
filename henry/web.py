from bottle import Bottle, request

from henry.coreconfig import (dbcontext, auth_decorator)
from henry.config import jinja_env

webmain = w = Bottle()


@w.get('/app')
@dbcontext
@auth_decorator(0)
def index():
    return jinja_env.get_template('base.html').render(user=user)

# @w.get('/app/client_stat/<uid>')
# @dbcontext
# @auth_decorator(0)
# def get_client_stat(uid):
#    start_date = datetime.date(2015, 7, 27)
#    end_date = datetime.datetime.now()
#    status = Status.COMITTED
#
#    result = list(invapi.search_metadata_by_date_range(
#        start_date, end_date, status, {'client_id': uid}))
#    payments = list(sessionmanager.session.query(NPayment).filter(
#        NPayment.client_id == uid))
#
#    all_data = [('COMPRA', r.uid, r.timestamp.date(), '', r.total / 100)
#                for r in result if r.payment_format != PaymentFormat.CASH]
#    all_data.extend((('PAGO ' + r.type, r.uid, r.date, r.value / 100, '') for r in payments))
#    all_data.sort(key=itemgetter(2), reverse=True)
#
#    compra = sum(r.total for r in result if r.payment_format != PaymentFormat.CASH) / 100
#    pago = sum(r.value for r in payments) / 100
#
#    temp = jinja_env.get_template('client_stat.html')
#    client = clientapi.get(uid)
#    return temp.render(client=client, activities=all_data, compra=compra, pago=pago)
