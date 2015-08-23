#  I am bad at naming
from henry.base.dbapi import DBApi, dbmix
from henry.schema.core import NCliente, NPriceList

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

price_override_name = (('prod_id', 'codigo'), ('cant_mayorista', 'threshold'))


class PriceList(dbmix(NPriceList, price_override_name)):

    @classmethod
    def deserialize(cls, dict_input):
        prod = super(cls, PriceList).deserialize(dict_input)
        if prod.multiplicador:
            prod.multiplicador = Decimal(prod.multiplicador)
        return prod
