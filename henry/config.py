from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from jinja2 import Environment, FileSystemLoader
from henry.helpers.fileservice import FileService
from henry.layer2.productos import ProductApiDB, TransApiDB
from henry.layer2.invoice import InvApiDB, InvApiOld


def create_mysql_string(user, password):
    return "mysql+mysqldb://%s:%s@%s/henry" % (user, password, CONFIG['ip'])

conn_string = 'mysql+mysqldb://root:no jodas@localhost/henry'
# conn_string = 'sqlite:////home/han/git/henryFACT/servidor/henry/test_db.sql'
engine = create_engine(conn_string)
sessionfactory = sessionmaker(bind=engine)
fileroot = '/var/data/ingreso'
prodapi = ProductApiDB(sessionfactory())
filemanager = FileService(fileroot)
transapi = TransApiDB(sessionfactory(), filemanager, prodapi)
invapi2 = InvApiOld(sessionfactory())

template_paths = ['./templates']
jinja_env = Environment(loader=FileSystemLoader(template_paths))
def id_type(uid):
    if uid == 'NA':
        return '07' # General
    elif len(uid) == 10:
        return '05' # cedula
    elif len(uid) == 13:
        return '04' # RUC
    else:
        return ''
jinja_env.globals.update(id_type=id_type)
