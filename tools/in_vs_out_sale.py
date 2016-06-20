import datetime
from collections import defaultdict

from decimal import Decimal

from coreapi import dbapi
from henry.config import transapi
from henry.coreconfig import invapi
from henry.dao.document import Status

start = datetime.date(2015, 9, 1)
end = datetime.date(2016, 5, 30)

def main():

    with dbapi.session:
        trans = transapi.search_metadata_by_date_range(start, end, other_filters={'dest': 1})
        invs = invapi.search_metadata_by_date_range(start, end, status=Status.COMITTED)
        trans_by_month = defaultdict(Decimal)
        sale_by_month = defaultdict(Decimal)


        for x in trans:
            key = (x.timestamp.year, x.timestamp.month)
            if x.status != Status.DELETED:
                trans_by_month[key] += x.value

        for x in invs:
            key = (x.timestamp.year, x.timestamp.month)
            sale_by_month[key] += Decimal(x.subtotal - (x.discount or 0)) / 100


        for x, y in sorted(sale_by_month.items()):
            print '\t'.join(map(str, [x, y, trans_by_month[x], y - trans_by_month[x]]))


if __name__ == '__main__':
    main()

