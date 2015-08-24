from sqlalchemy import (Column, Integer, DateTime, String,
                        ForeignKey, Numeric)
from sqlalchemy.orm import relationship, backref
from henry.schema.base import Base


class NInventoryRevision(Base):
    __tablename__ = 'revisiones_de_inventario'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    bodega_id = Column(Integer)
    timestamp = Column(DateTime, index=True)
    created_by = Column(String(20))
    status = Column(String(10))
    items = relationship('NInventoryRevisionItem', backref=backref('revision'))


class NInventoryRevisionItem(Base):
    __tablename__ = 'items_de_revisiones'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    revision_id = Column(Integer, ForeignKey(NInventoryRevision.uid))
    prod_id = Column(String(20), index=True)
    inv_cant = Column(Numeric(20, 3))
    real_cant = Column(Numeric(20, 3))


class NTransferencia(Base):
    __tablename__ = 'transferencias'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    status = Column(String(10))

    origin = Column(Integer)
    dest = Column(Integer)

    trans_type = Column(String(10))
    ref = Column(String(100))
    value = Column(Numeric(11, 4))

    # unix filepath where the items is stored
    items_location = Column(String(200))
