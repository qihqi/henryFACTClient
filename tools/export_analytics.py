import sys
import datetime

from henry.analytics.exporting import export

__author__ = 'han'

# This script will export the data in the database into
# json files. One file per day per type.
# current types are: sale-<date>.json and transfer-<date>.json

DIRECTORY = '/var/data/exports/'
URL = 'http://192.168.0.22'


def main():
    parse_date = datetime.datetime.strptime
    dump_date = (parse_date(sys.argv[1], '%Y-%m-%d')
                 if len(sys.argv) > 1 else datetime.date.today())
    export(dump_date, DIRECTORY, URL)


if __name__ == '__main__':
    main()
