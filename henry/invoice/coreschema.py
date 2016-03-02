from sqlalchemy import Column, Integer, DateTime, String, Boolean, Index
from henry.schema.base import Base

__author__ = 'han'


class NNota(Base):
    __tablename__ = 'notas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    status = Column(String(10))

    # this pair should be unique
    codigo = Column(String(20))
    almacen_id = Column(Integer)
    almacen_name = Column(String(20))
    almacen_ruc = Column(String(20))

    client_id = Column(String(20))
    user_id = Column(String(20))
    paid = Column(Boolean)
    paid_amount = Column(Integer)
    payment_format = Column(String(20))

    subtotal = Column(Integer)  # sum of items
    # amount of money received total = subtotal - discount + iva - retension
    total = Column(Integer)
    tax = Column(Integer)
    retension = Column(Integer)  # (TODO) have to deprecate
    discount = Column(Integer)
    tax_percent = Column(Integer)
    discount_percent = Column(Integer)

    bodega_id = Column(Integer)
    # unix filepath where the items is stored
    items_location = Column(String(200))

Index('ix_notas_2', NNota.almacen_id, NNota.codigo)

class NPedidoTemporal(Base):
    __tablename__ = 'pedidos_temporales'
    id = Column(Integer, autoincrement=True, primary_key=True)
    client_lastname = Column(String(20), index=True)
    user = Column(String(20))
    total = Column(Integer)
    timestamp = Column(DateTime)
    status = Column(String(10))
    external_id = Column(Integer)
