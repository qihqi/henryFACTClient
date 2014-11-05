from henry.helpers.serialization import SerializableMixin
from henry.layer1.schema import NCliente


class Client(SerializableMixin, NCliente):
    _name = (
        'codigo',
        'nombres',
        'apellidos',
        'direccion',
        'ciudad',
        'telefono',
        'tipo',
        'cliente_desde',)


class ClientApiDB(object):

    def __init__(self, smanager):
        self.manager = smanager

    def get(self, cliente_id):
        cliente = self.manager.session.query(Client).filter(
            Client.codigo == cliente_id)
        return cliente.first()

    def search(self, apellido):
        session = self.manager.session
        clientes = session.query(Client).filter(
            NCliente.apellidos.startswith(apellido))
        return clientes

    def save(self, cliente):
        newc = cliente
        if not isinstance(cliente, NCliente):
            newc = NCliente(codigo=cliente.codigo,
                            nombres=cliente.nombres,
                            apellidos=cliente.apellidos,
                            direccion=cliente.direccion,
                            telefono=cliente.telefono,
                            ciudad=cliente.ciudad,
                            tipo=cliente.tipo,
                            cliente_desde=cliente.cliente_desde
                            )
        session = self.manager.session
        session.add(newc)
        session.flush()
