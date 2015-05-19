import json
from henry.layer1.schema import NVenta, NItemVenta, NOrdenDespacho, NItemDespacho
from henry.layer1.schema import NProducto, NContenido, NCliente
from henry.config import new_session

def authenticate(username, password, userinfo):
    s = sha.new(password)
    return s.hexdigest() == userinfo.password


def get_user_info(session, username):
    return session.query(NUsuario).filter_by(username=username).first()


def get_cliente_by_id(cliente_id):
    session = new_session()
    cliente = session.query(NCliente).filter(NCliente.codigo == cliente_id)
    return cliente.first()


def search_cliente(apellido):
    session = new_session()
    clientes = session.query(NCliente).filter(NCliente.apellidos.startswith(apellido))
    return clientes


def create_cliente(cliente):
    newc = NCliente(codigo=cliente.codigo,
                    nombres=cliente.nombres,
                    apellidos=cliente.apellidos,
                    direccion=cliente.direccion,
                    telefono=cliente.telefono,
                    ciudad=cliente.ciudad,
                    tipo=cliente.tipo,
                    cliente_desde=cliente.cliente_desde
                    )
    session = new_session()
    session.add(newc)
    session.commit()
    return newc
