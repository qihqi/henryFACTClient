from sqlalchemy import Column, Integer, DateTime, String, Boolean, Index
from henry.schema.base import Base

__author__ = 'han'

class NSRINota(Base):
    __tablename__ = 'sri_notas'

    # id
    uid = Column(Integer, primary_key=True, autoincrement=True)

    almacen_ruc = Column(String(100))
    orig_codigo = Column(String(100))
    
    # original timestamp == when is this created by client on their time
    timestamp_received = Column(DateTime, index=True)
    status = Column(String(10))

    # unix filepath where the items is stored
    json_inv_location = Column(String(200))

    # this is what is send to sri
    xml_inv_location = Column(String(200))
    
    # send response
    resp1_location = Column(String(200))
    resp2_location = Column(String(200))
