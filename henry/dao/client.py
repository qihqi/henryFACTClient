from sqlalchemy.exc import IntegrityError
from henry.base.serialization import SerializableMixin
from henry.base.schema import NCliente
from henry.dao.exceptions import ItemAlreadyExists


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

    def get(self, cliente_id):
        cliente = self.manager.session.query(Client).filter(
            Client.codigo == cliente_id)
        return cliente.first()

    def search(self, apellido):
        session = self.manager.session
        clientes = session.query(Client).filter(
            NCliente.apellidos.startswith(apellido))
        return clientes

    def create(self, cliente):
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
        try:
            session.add(newc)
            session.flush()
        except IntegrityError:
            raise ItemAlreadyExists('client {} already exists'.format(newc.codigo))

    def update(self, client_id, new_content):
        self.manager.session.query(
            NCliente).filter_by(codigo=client_id).update(
            new_content)
