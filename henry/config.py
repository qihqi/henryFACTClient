from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


CONFIG = {
    'connection_string': 'mysql+mysqldb://root:no jodas@localhost/henry',
    'echo': True,
    'ip': 'localhost',
}


def get_engine():
    if not get_engine.engine:
        print CONFIG
        engine = create_engine(CONFIG['connection_string'], echo=CONFIG['echo'])
    return get_engine.engine
get_engine.engine = None


def new_session():
    if not new_session.session_class:
        new_session.session_class = sessionmaker(bind=get_engine())
    return new_session.session_class()
new_session.session_class = None


def create_mysql_string(user, password):
    return "mysql+mysqldb://%s:%s@%s/henry" % (user, password, CONFIG['ip'])
