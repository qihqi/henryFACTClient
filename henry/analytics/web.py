import datetime

from bottle import request, Bottle
import bottle

from henry.base.serialization import json_dumps
from henry.analytics.report import ExportManager
from henry.base.common import parse_start_end_date

app = Bottle()
BASEDIR = '/var/data/exports'
invmanager = ExportManager(BASEDIR, 'sale', 'http://192.168.0.22')


def timerange(start, end, delta=datetime.timedelta(days=1)):
    x = start
    while x <= end:
        yield x
        x += delta


@app.get('/app/analytics/daily')
def all_daily_stats():
    start, end = parse_start_end_date(request.query)
    if end is None:
        end = datetime.date.today()
    if start is None:
        start = end - datetime.timedelta(days=7)

    result = {}
    for x in timerange(start, end):
        if x.isoweekday() != 7:  # skips Sundays
            report = invmanager.get(x)
            if report is not None:
                result[x.isoformat()] = (report.total_count,
                                         report.total_value, report.total_tax)
            else:
                result[x.isoformat()] = None
    return result


@app.post('/app/analytics/reload/<day>')
def reload_analytics(day):
    day = datetime.datetime.strptime(day, '%Y-%m-%d').date()
    invmanager.reload_analytics(day)
    return {'status': 'success'}


@app.get('/app/analytics/daily/<day>')
def get_daily_stats_fine(day):
    day = datetime.datetime.strptime(day, '%Y-%m-%d').date()
    report = invmanager.get(day)
    if report is None:
        return None
    return json_dumps({
        'total': report.total_value,
        'count': report.total_count,
        'by_client': report.by_client,
        'by_type': report.by_type,
    })


if __name__ == '__main__':
    bottle.run(app, host='0.0.0.0', debug=True, port=8080)
