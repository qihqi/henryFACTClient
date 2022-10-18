from sqlalchemy import Column, String, Integer, DateTime, Numeric, Index
from henry.schema.base import Base

__author__ = 'han'


class NEntity(Base):
    __tablename__ = 'entities'
    codename = Column(String(10), primary_key=True)
    name = Column(String(20))
    desc = Column(String(50))


class NInventory(Base):
    __tablename__ = 'inventories'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    entity_codename = Column(String(10))
    external_id = Column(Integer)
    inventory_id = Column(Integer)
    name = Column(String(20))


class NSale(Base):  # nominal sale
    __tablename__ = 'sales'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    client_id = Column(String(20))

    seller_codename = Column(String(20))
    seller_ruc = Column(String(20))
    seller_inv_uid = Column(Integer)  # uid of document
    invoice_code = Column(String(10))  # codigo

    pretax_amount_usd = Column(Numeric(15, 4), default=0)
    tax_usd = Column(Numeric(15, 4), default=0)
    status = Column(String(10))

    user_id = Column(String(20))
    payment_format = Column(String(20))


Index('ix_sales_2', NSale.seller_codename, NSale.seller_inv_uid)


class NInvMovementMeta(Base):
    __tablename__ = 'inv_movements'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    inventory_codename = Column(String(10))
    inventory_docid = Column(Integer)

    timestamp = Column(DateTime, index=True)
    status = Column(String(10))

    origin = Column(Integer)
    dest = Column(Integer)

    trans_type = Column(String(10))
    value_usd = Column(Numeric(11, 4), default=0)

    # unix filepath where the items is stored
    items_location = Column(String(200))


Index('ix_inv_mov_2', NInvMovementMeta.inventory_codename,
      NInvMovementMeta.inventory_docid, NInvMovementMeta.trans_type)
