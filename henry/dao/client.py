from henry.base.dbapi import DBApi, dbmix
from henry.schema.core import NCliente

class Client(dbmix(NCliente)):

    @property
    def fullname(self):
        nombres = self.nombres
        if not nombres:
            nombres = ''
        apellidos = self.apellidos
        if not apellidos:
            apellidos = ''
        return apellidos + ' ' + nombres


class ClientApiDB(object):

    def __init__(self, smanager):
        self.manager = smanager
        self.api = DBApi(smanager, Client)

    def get(self, cliente_id):
        return self.api.get(cliente_id)

    def search(self, apellido):
        return self.api.search(**{'apellidos-prefix': apellido})

    def create(self, cliente):
        return self.api.create(cliente)

    def update(self, client_id, new_content):
        return self.api.update(client_id, new_content)
