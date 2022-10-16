from sqlalchemy import Column, Integer, DateTime, String, Boolean, Index, Numeric
from henry.schema.base import Base

__author__ = 'han'

class NSRINota(Base):
    __tablename__ = 'sri_notas'

    # id
    uid = Column(Integer, primary_key=True, autoincrement=True)

    almacen_id = Column(Integer)
    almacen_ruc = Column(String(100))
    orig_codigo = Column(String(100))
    orig_timestamp = Column(DateTime)
    buyer_ruc = Column(String(30))
    buyer_name = Column(String(100))

    total = Column(Numeric(11, 4))
    tax = Column(Numeric(11, 4))
    discount = Column(Numeric(11, 4))
    access_code = Column(String(50))

    # original timestamp == when is this created by client on their time
    timestamp_received = Column(DateTime, index=True)
    # last status of communication
    status = Column(String(20))

    # unix filepath where the items is stored
    json_inv_location = Column(String(200))
    xml_inv_location = Column(String(200))
    xml_inv_signed_location = Column(String(200))

    # path to a json file with communications with remote
    all_comm_path = Column(String(200))

