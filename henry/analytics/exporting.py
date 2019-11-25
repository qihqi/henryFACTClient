from __future__ import print_function
import datetime
import os
import sys
import requests

__author__ = 'han'


def dump_content(ddate, dest_dir, prefix, listurl, itemurl):
    params = {
        'start_date': ddate.isoformat(),
        'end_date': (ddate + datetime.timedelta(days=1)).isoformat()
    }
    all_items = requests.get(listurl, params=params).json()
    fname = '{}-{}.txt'.format(prefix, ddate.isoformat())
    fullpath = os.path.join(dest_dir, fname)
    with open(fullpath, 'w') as f:
        for x in all_items:
            inv = requests.get('{}/{}'.format(itemurl, x['uid']))
            if inv.status_code != 200:
                print(inv.text, file=sys.stderr)
                continue
            f.write(inv.text)
            f.write('\n')


def export(ddate, dest, baseurl):
    dump_content(ddate, dest, 'sale', baseurl + '/app/api/nota', baseurl + '/api/nota')
    dump_content(ddate, dest, 'trans', baseurl + '/app/api/ingreso', baseurl + '/app/api/ingreso')