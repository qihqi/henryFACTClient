import datetime

from henry.accounting.reports import get_sale_report_full
from henry.base.serialization import json_dumps
from henry.coreconfig import invapi


def main():

    start = datetime.date(2015, 7, 1)
    end = datetime.date(2016, 5, 1)

    while start < end:
        report = get_sale_report_full(invapi, start, end)
        with open(start.isoformat() + '-report.json') as f:
            f.write(json_dumps(report))
            f.flush()
main()