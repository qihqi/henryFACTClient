import json

from sqlalchemy.sql import select

from henry.layer1.schema import NProducto, NContenido, NCliente
from henry.config import new_session


def _prod_query(session):
    return session.query(NProducto, NContenido).filter(NProducto.codigo == NContenido.prod_id)


def get_product_by_id(codigo, bodega_id):
    session = new_session()
    prod = _prod_query(session).filter(
        NContenido.bodega_id == bodega_id
    ).filter(
        NContenido.prod_id == codigo
    ).first()

    return prod


def search_product(prefix):
    session = new_session()
    prod = _prod_query(session).filter(
        NProducto.nombre.startswith(prefix)
    )
    return prod


def create_producto(codigo, nombre, precio1, precio2,
                    bodega):
    prod = NProducto(codigo=codigo, nombre=nombre)
    cont = NContenido(prod_id=codigo, bodega_id=bodega,
                      precio=precio1, precio2=precio2,
                      cant=0, cant_mayorista=0)
    session = new_session()
    session.add(prod)
    session.add(cont)
    session.commit()


def serialize_product(product_row):
    if not product_row:
        return 'None'
    return json.dumps({
        'codigo': product_row.codigo,
        'precio': str(product_row.precio),
        'nombre': product_row.nombre
    })


def get_cliente_by_id(cliente_id):
    session = new_session()
    cliente = session.query(NCliente).filter(NCliente.codigo == cliente_id).first()
    return cliente


def search_cliente(apellido):
    session = new_session()
    clientes = session.query(NCliente).filter(NCliente.apellidos.startswith(apellido))
    return clientes


def get_nota_de_venta(id):
    metadata_query = select([Schemas.nota_de_venta]).where(Schemas.nota_de_venta.c.id == id)
    row_query = select([Schemas.item_de_venta,
                        Schemas.producto.c.nombre,
                        Schemas.contenido.c.precio,
                        Schemas.contenido.c.precio2]).where(
        (Schemas.item_de_venta.c.venta_cod_id == id) &
        (Schemas.producto.c.codigo == Schemas.item_de_venta.c.producto_id) &
        (Schemas.contenido.c.prod_id == Schemas.item_de_venta.c.producto_id))

    engine = get_database_connection()

    nota = engine.execute(metadata_query).fetchone()
    rows = engine.execute(row_query)

    return create_full_nota(nota, rows)


def create_full_nota(nota, rows):
    def serialize_item(item):
        return {
            'codigo': item.producto_id,
            'nombre': item.nombre,
            'cantidad': str(item.cantidad),
            'precio': str(item.precio)}

    item_list = map(serialize_item, rows)
    return json.dumps({
        'cliente': {
            'id': nota.cliente_id
        },
        'items': item_list
    })




