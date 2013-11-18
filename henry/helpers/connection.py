from sqlalchemy import create_engine


def get_database_connection():
    if not get_database_connection.engine:
        get_database_connection.engine = create_engine(
                'mysql://root:no jodas@localhost/henry')
    return get_database_connection.engine
get_database_connection.engine = None
