from sqlalchemy import Column, Integer, String, DateTime, Index
from henry.schema.base import Base

__author__ = 'han'


class ObjType:
    INV = 'notas'
    TRANS = 'transfer'
    CHECK = 'cheque'


class NComment(Base):
    __tablename__ = 'comentarios'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    objtype = Column(String(20))
    objid = Column(String(20))
    timestamp = Column(DateTime)
    user_id = Column(String(10))
    comment = Column(String(200))

Index('ix_comment_2', NComment.objtype, NComment.objid)
