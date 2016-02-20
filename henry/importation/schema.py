from sqlalchemy import Integer, Column, String, DateTime, Numeric
from henry.schema.base import Base


class NUniversalProduct(Base):
    __tablename__ = 'universal_products'
    upi = Column(Integer, primary_key=True, autoincrement=True)
    name_es = Column(String(50), index=True)  # searchable name
    name_zh = Column(String(50), index=True)  # searchable name

    providor_zh = Column(String(20), index=True)  # may replace by id
    providor_item_id = Column(String(20))

    selling_id = Column(String(20))  # id we use to sell
    declaring_id = Column(Integer)  # id we use to sell
    material = Column(String(20))
    unit = Column(String(20))

    description = Column(String(200))
    thumbpath = Column(String(200))


class NDeclaredGood(Base):
    __tablename__ = 'declared_good'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    display_name = Column(String(100))
    display_price = Column(Numeric(15, 4))



# container = set of invoices
# each invoice -> single provedor, set of items
# could several providor go for the same item?

class NPurchase(Base):
    __tablename__ = 'purchases'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime)
    providor = Column(String(20))
    total_rmb = Column(Numeric(15, 4))


class NPurchaseItem(Base):
    __tablename__ = 'purchase_items'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    upi = Column(Integer)
    purchase_id = Column(Integer)
    color = Column(String(20))
    quantity = Column(Numeric(11, 3))
    price_rmb = Column(Numeric(15, 4))



