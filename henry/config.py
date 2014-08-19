from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from jinja2 import Environment, FileSystemLoader
from henry.helpers.fileservice import FileService
from henry.layer2.productos import ProductApiDB, TransApiDB


def create_mysql_string(user, password):
    return "mysql+mysqldb://%s:%s@%s/henry" % (user, password, CONFIG['ip'])

conn_string = 'mysql+mysqldb://root:no jodas@localhost/henry'
# conn_string = 'sqlite:////home/han/git/henryFACT/servidor/henry/test_db.sql'
engine = create_engine(conn_string)
sessionfactory = sessionmaker(bind=engine)
fileroot = '/tmp'
prodapi = ProductApiDB(sessionfactory())
filemanager = FileService(fileroot)
transapi = TransApiDB(sessionfactory(), filemanager, prodapi)

template_paths = ['./templates']
jinja_env = Environment(loader=FileSystemLoader(template_paths))
