from sqlalchemy.exc import IntegrityError
from henry.base.serialization import SerializableMixin, DbMixin
from henry.base.schema import NCliente
from henry.dao.exceptions import ItemAlreadyExists


class Client(SerializableMixin, DbMixin):
    _db_class = NCliente

    _name = (
        'codigo',
        'nombres',
        'apellidos',
        'direccion',
        'ciudad',
        'telefono',
        'tipo',
        'cliente_desde',)
    _db_attr = _name

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
        cliente = self.manager.session.query(NCliente).filter(
            NCliente.codigo == cliente_id).first()
        return Client.from_db_instance(cliente)

    def search(self, apellido):
        session = self.manager.session
        clientes = session.query(NCliente).filter(
            NCliente.apellidos.startswith(apellido))
        return map(Client.from_db_instance, clientes)

    def create(self, cliente):
        newc = cliente.db_instance()
        session = self.manager.session
        try:
            session.add(newc)
            session.commit()
        except IntegrityError:
            session.rollback()
            raise ItemAlreadyExists('client {} already exists'.format(newc.codigo))

    def update(self, client_id, new_content):
        self.manager.session.query(
            NCliente).filter_by(codigo=client_id).update(
            new_content)
