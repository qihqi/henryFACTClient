from builtins import object
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from henry.base.dbapi import DBApiGeneric
from henry.base.session_manager import SessionManager
from henry.schema.base import Base

class FakeTransaction(object):

    def __init__(self):
        pass

    def bulk_save(self, _):
        pass

    def save(self, _):
        pass

def make_test_dbapi():
    engine = create_engine('sqlite:///:memory:', echo=False)
    sessionfactory = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    manager = SessionManager(sessionfactory)
    dbapi = DBApiGeneric(manager)
    return dbapi
