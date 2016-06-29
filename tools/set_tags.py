import datetime
import json
from collections import defaultdict

from decimal import Decimal

from coreapi import dbapi
from henry.accounting.reports import SaleReport
from henry.product.dao import ProdTag, ProdTagContent, ProdItemGroup
from henry.product.schema import NItemGroup, NProdTagContent


def main():
    with dbapi.session:
       # x = ProdTag(tag='hot_items', description='70 best sellers that contribute to 50% of revenue', created_by='han qi')
       # dbapi.create(x)
       # dbapi.db_session.commit()

        with open('tags.txt') as f:
            for x in f.readlines():
                tag, prod_id = x.strip().split()[:2]
                itemgroup = dbapi.getone(ProdItemGroup, prod_id=prod_id)
                if itemgroup is None:
                    print 'missing', prod_id
                    continue
                if dbapi.getone(ProdTagContent, tag=tag, itemgroup_id=itemgroup.uid) is None:
                    dbapi.create(ProdTagContent(tag=tag, itemgroup_id=itemgroup.uid))
                    print 'created itemgroup', itemgroup.uid
            dbapi.db_session.commit()


def incr_month(start):
    year = start.year
    month = start.month
    month += 1
    if month > 12:
        month -= 12
        year += 1
    return datetime.date(year, month, start.day)


def main2():

    start = datetime.date(2015, 8, 1)
    end = datetime.date(2016, 5, 1)

    top_100 = {}
    while start < end:
        print start.isoformat()
        with open('reports/{}-report.json'.format(start.isoformat())) as f:
            report = SaleReport.deserialize(json.loads(f.read()))
            top = sorted(report.best_sellers, key=lambda i: Decimal(i[1]['value']))[-10:]
            top_100[start.isoformat()] = set(x[0].upper() for x in top)
            start = incr_month(start)

    prev = None
    for x, y in sorted(top_100.items()):
        y = set(y)
        if prev is None:
            prev = y
        print x, len(prev)
        prev = prev | y
        print prev

def main3():
    all_tags = defaultdict(list)
    with dbapi.session:
        for prod_id, tag in dbapi.db_session.query(NItemGroup.prod_id, NProdTagContent.tag).filter(
                        NItemGroup.uid == NProdTagContent.itemgroup_id):
            all_tags[prod_id.upper()].append(tag)
    values_by_tag = defaultdict(Decimal)
    with open('all.report') as f:
        report = SaleReport.deserialize(json.loads(f.read()))
        total = sum(map(Decimal, report.mayor.values())) + sum(map(Decimal, report.menor.values()))
        for prod, other in report.best_sellers:
            if prod not in all_tags or all_tags[prod] == ['hot_items']:
                values_by_tag['no_tag'] += Decimal(other['value'])
            for tag in all_tags[prod]:
                values_by_tag[tag] += Decimal(other['value'])

    for x, y in values_by_tag.items():
        print x, y, y/total



main3()
