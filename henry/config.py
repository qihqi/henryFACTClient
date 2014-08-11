from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from henry.helpers.fileservice import FileService
from henry.layer2.productos import ProdApiDB, TransApiDB

def create_mysql_string(user, password):
    return "mysql+mysqldb://%s:%s@%s/henry" % (user, password, CONFIG['ip'])

conn_string = 'mysql+mysqldb://root:no jodas@localhost/henry',
engine = create_engine(conn_string)
sessionfactory = sessionmaker(bind=engine)
fileroot = '/tmp'
prodapi = ProdApiDB(sessionfactory())
filemanager = FileService(fileroot)
transapi = TransApiDB(sessionfactory(), filemanager, prodapi)
