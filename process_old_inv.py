from collections import defaultdict
import datetime
import os
import json
# from matplotlib.pyplot import plt

from henry.dao.order import Invoice

DIR = '/home/han/Downloads/invold'


def stream_inv(prefix, start_date, end_date):
    delta = datetime.timedelta(days=1)
    while start_date <= end_date:
        fname = os.path.join(DIR, '{}-{}.txt'.format(prefix, start_date.isoformat()))
        if os.path.exists(fname):
            with open(fname) as f:
                for line in f.xreadlines():
                    yield Invoice.deserialize(json.loads(line))
        start_date += delta


def make_bar_graph(list_of_pairs):
    x_value = [x[0] for x in list_of_pairs]
    y_value = [x[1] for x in list_of_pairs]
    start = list_of_pairs[0][0]
    
    pos = [(x - start).day for x in x_value]
    
    fig, ax = plt.subplots()
    bar = ax.bar(pos, y_value, 0.3, color='r')
    plt.show()

def make_graph(list_of_pairs):

    for x, y in list_of_pairs:
        print x.isoweekday(), x.isoformat(),
        print '=' * (y / 50000)



def main():
    start_date = datetime.date(2012, 1, 1)
    end_date = datetime.date(2014, 12, 31)

    sales_by_date = defaultdict(int)
    for i in stream_inv('inv', start_date, end_date):
        sales_by_date[i.meta.timestamp.date()] += (i.meta.total or 0)
    
    print sorted(sales_by_date.items())
    make_graph(sorted(sales_by_date.items()))

main()

