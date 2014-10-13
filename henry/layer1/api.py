import json
from henry.layer1.schema import NVenta, NItemVenta, NOrdenDespacho, NItemDespacho
from henry.layer1.schema import NProducto, NContenido, NCliente
from henry.config import new_session

def get_all_users():
    session = sessionfactory()
    return session.query(NUsuario)


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
