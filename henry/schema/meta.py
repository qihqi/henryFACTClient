from sqlalchemy import Column, Integer, String, DateTime, Index
from henry.schema.base import Base

__author__ = 'han'


class ObjType:
    INV = 'notas'
    TRANS = 'transfer'
    CHECK = 'cheque'
    PROD = 'prod'
    TODO = 'todo'
    ACCOUNT = 'acct'


class NComment(Base):
    __tablename__ = 'comentarios'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    objtype = Column(String(20))
    objid = Column(String(20))
    timestamp = Column(DateTime)
    user_id = Column(String(10))
    comment = Column(String(200))

Index('ix_comment_2', NComment.objtype, NComment.objid)


class NImage(Base):
    __tablename__ = 'images'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    objtype = Column(String(20))
    objid = Column(String(20))
    imgtag = Column(String(20))
    path = Column(String(100))

Index('ix_image_2', NImage.objtype, NImage.objid)


class NTodo(Base):
    __tablename__ = 'todos'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    objtype = Column(String(20))
    objid = Column(String(20))
    msg = Column(String(100))
    status = Column(String(20))
    due_date = Column(DateTime)
    creation_date = Column(DateTime)

Index('ix_todo_2', NImage.objtype, NImage.objid)
