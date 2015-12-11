import os
import sys
import datetime
import requests

__author__ = 'han'

# This script will export the data in the database into
# json files. One file per day per type.
# current types are: sale-<date>.json and transfer-<date>.json

DIRECTORY = '/var/data/exports/'
URL = 'http://192.168.0.22'


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
                print >>sys.stderr, inv.text
                continue
            f.write(inv.text)
            f.write('\n')

def export(ddate, dest):
    dump_content(ddate, dest, 'sale', URL + '/app/api/nota', URL + '/api/nota')
    dump_content(ddate, dest, 'trans', URL + '/app/api/ingreso', URL + '/app/api/ingreso')


def main():
    parse_date = datetime.datetime.strptime
    dump_date = (parse_date('%Y-%m-%D', sys.argv[1])
                 if len(sys.argv) > 1 else datetime.date.today())
    export(dump_date, DIRECTORY)


if __name__ == '__main__':
    main()
