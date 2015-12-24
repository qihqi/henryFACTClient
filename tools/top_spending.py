from collections import defaultdict
from operator import itemgetter
import datetime
from henry.coreconfig import invapi, clientapi
from henry.coreconfig import sessionmanager
from henry.dao.document import Status
from henry.dao.order import PaymentFormat
from henry.accounting.acct_schema import NPayment
from henry.schema.inv import NNota

all_compra = defaultdict(list)
all_pago = defaultdict(list)

def populate():
    start_date = datetime.date(2015, 6, 1)
    end_date = datetime.datetime.now()
    status = Status.COMITTED
    for x in sessionmanager.session.query(NNota).filter_by(status=Status.COMITTED):
        all_compra[x.client_id].append(x)
    for x in sessionmanager.session.query(NPayment):
        all_pago[x.client_id].append(x)


def get_spent_and_payment(uid):
    result = all_compra[uid]
    payments = all_pago[uid]

    compra_efectivo = sum((r.total for r in result if r.payment_format == PaymentFormat.CASH))
    compra = sum((r.total for r in result if r.payment_format != PaymentFormat.CASH))
    pago = sum((r.value for r in payments))
    return compra_efectivo, compra, pago


def main():
    all_client = []
    with sessionmanager as session:
        populate()
        for c in clientapi.search():
            comprae, compra, pago = get_spent_and_payment(c.codigo)
            all_client.append((c, comprae, compra, pago))

    all_client.sort(key=lambda x: x[1] + x[2], reverse=True)

    i = 0
    for x in all_client:
        print '\t'.join((x[0].apellidos, x[0].codigo, str(x[1]), str(x[2]), str(x[3])))
        i += 1
        if i > 100:
            break

main()
