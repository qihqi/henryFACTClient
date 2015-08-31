import sys
from decimal import Decimal
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Numeric
 
Base = declarative_base()

class ItemGroup(Base):
    __tablename__ = 'item_groups'
    item_group_id = Column(Integer, primary_key=True, autoincrement=True)
    provider_cn = Column(String(100))
    name_cn = Column(String(100))
    name_es = Column(String(100))
    price_rmb = Column(Numeric(14, 2))
    henry_prod_id = Column(String(10))
    henry_name_es = Column(String(10))
    henry_price_usd = Column(Numeric(14, 2))
    image_path = Column(String(100))

engine = create_engine('?charset=utf8')
sessionfactory = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def main():
    session = sessionfactory()
    with open(sys.argv[1]) as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        provider = None
        for row in reader:
            if row[0]:
                new_provider = row[0].decode('utf8')
                if new_provider == u'\u5408\u8ba1':
                    continue
                provider = new_provider
            new_item = ItemGroup()
            new_item.name_cn = row[1].decode('utf8')
            price_rmb = row[3].decode('utf8')
            try:
                price_rmb = Decimal(filter(lambda x: x.isdigit() or x == u'.', price_rmb))
            except:
                for x in row:
                    print x, 
                    print
                continue
            new_item.price_rmb = price_rmb
            session.add(new_item)
    session.commit() 

if __name__ == '__main__':
    main()




