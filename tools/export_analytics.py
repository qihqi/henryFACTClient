import sys
import datetime

from henry.analytics.exporting import export

__author__ = 'han'

# This script will export the data in the database into
# json files. One file per day per type.
# current types are: sale-<date>.json and transfer-<date>.json

DIRECTORY = './invold'
URL = 'http://192.168.0.22'


def main():
    start_date = datetime.date(2015, 1, 31)
    end_date = datetime.date(2016, 3, 23)
    parse_date = datetime.datetime.strptime
    while start_date <= end_date:
        export(start_date, DIRECTORY, URL)
        print 'date', start_date
        start_date += datetime.timedelta(days=1)


if __name__ == '__main__':
    main()
