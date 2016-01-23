import datetime
from decimal import Decimal
from bottle import abort

__author__ = 'han'


def parse_iso(date_string):
    return datetime.datetime.strptime(date_string, '%Y-%m-%d')


def parse_start_end_date(forms, start_name='start', end_name='end'):
    start = forms.get(start_name, None)
    end = forms.get(end_name, None)
    try:
        if start:
            start = parse_iso(start)
        else:
            start = None
        if end:
            end = parse_iso(end)
        else:
            end = None
    except:
        abort(400, 'Fecha en formato equivocada')
    return start, end


def convert_to_cent(dec):
    if not isinstance(dec, Decimal):
        dec = Decimal(dec)
    return int(dec * 100)


def parse_start_end_date_with_default(form, start, end):
    newstart, newend = parse_start_end_date(form)
    if newend is None:
        newend = end
    if newstart is None:
        newstart = start
    if isinstance(newstart, datetime.datetime):
        newstart = newstart.date()
    if isinstance(newend, datetime.datetime):
        newend = newend.date()
    return newstart, newend
