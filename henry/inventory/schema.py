from sqlalchemy import (Column, Integer, DateTime, String,
                        Numeric)

from henry.schema.base import Base


class NTransferencia(Base):
    __tablename__ = 'transferencias'

    uid = Column('id', Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    status = Column(String(10))

    origin = Column(Integer)
    dest = Column(Integer)

    trans_type = Column(String(10))
    ref = Column(String(100))
    value = Column(Numeric(11, 4))

    # unix filepath where the items is stored
    items_location = Column(String(200))


class NRevisionMetadata(Base):
    __tablename__ = 'revisiones'

    uid = Column('id', Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    status = Column(String(10))

    user = Column(String(20))
    bodega_id = Column(Integer)

    # unix filepath where the items is stored
    items_location = Column(String(200))
