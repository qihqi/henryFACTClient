from henry.base.dbapi import dbmix
from henry.users.schema import NUsuario, NCliente

__author__ = 'han'
User = dbmix(NUsuario)


class Client(dbmix(NCliente)):  # type: ignore

    @property
    def fullname(self):
        nombres = self.nombres
        if not nombres:
            nombres = ''
        apellidos = self.apellidos
        if not apellidos:
            apellidos = ''
        return apellidos + ' ' + nombres