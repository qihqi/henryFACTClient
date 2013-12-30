from henry.server import app
import cred
from henry import config

connection_string = config.create_mysql_string(cred.U, cred.P)
config.CONFIG['connection_string'] = connection_string
config.CONFIG['echo'] = False
application = app
