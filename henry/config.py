from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


CONFIG = {
    'connection_string': 'sqlite:///:memory:',
    'echo': True,
}


def get_engine():
    if not get_engine.engine:
        engine = create_engine(CONFIG['connection_string'], CONFIG['echo'])
    return get_engine.engine
get_engine.engine = None


def new_session():
    if not get_session.session:
        get_session.session_class = sessionmaker(bind=get_engine())
    return get_session.session_class()
get_session.session_class = None