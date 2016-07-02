from sqlalchemy import Integer, Column, String, DateTime, Numeric, Index
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
    last_edit_timestamp = Column(DateTime)
    providor = Column(String(20))
    total_rmb = Column(Numeric(15, 4))

    created_by = Column(String(20))
    total_box = Column(Integer)
    total_gross_weight_kg = Column(Numeric(10, 3))


class NPurchaseItem(Base):
    __tablename__ = 'purchase_items'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    upi = Column(Integer)
    purchase_id = Column(Integer)
    color = Column(String(20))
    quantity = Column(Numeric(11, 3))
    price_rmb = Column(Numeric(15, 4))
    box = Column(Numeric(11, 3))


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
    seller_inv_uid = Column(Integer) # uid of document
    invoice_code = Column(String(10)) # codigo

    pretax_amount_usd = Column(Numeric(15, 4), default=0)
    tax_usd = Column(Numeric(15, 4), default=0)
    status = Column(String(10))

    client_id = Column(String(20))
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
