import json
from henry.layer1.schema import NVenta, NItemVenta, NOrdenDespacho, NItemDespacho
from henry.layer1.schema import NProducto, NContenido, NCliente
from henry.config import new_session


def _prod_query(session):
    return session.query(NContenido).join(NProducto, NContenido.prod_id == NProducto.codigo)


def get_product_by_id(codigo, bodega_id):
    session = new_session()
    cont = _prod_query(session).filter(
        NContenido.bodega_id == bodega_id
    ).filter(
        NContenido.prod_id == codigo
    ).first()

    return cont


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
    return cont


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


def get_nota_de_venta_by_id(codigo):
    session = new_session()
    metadata = session.query(NVenta).filter(NVenta.id == codigo).first()
    rows = session.query(NItemVenta).filter(NItemVenta.venta_cod_id == codigo).all()
    return serialize_nota(metadata, rows)


def serialize_nota(nota, rows):
    def serialize_item(item):
        cont = get_product_by_id(item.producto_id, nota.bodega_id)
        try:
            return {
                'codigo': cont.prod_id.decode('latin1'),
                'nombre': cont.producto.nombre.decode('latin1'),
                'cantidad': str(item.cantidad),
                'precio': int(cont.precio * 100)}
        except UnicodeDecodeError:
            print prod.codigo
            raise

    item_list = map(serialize_item, rows)
    print item_list
    return {
        'cliente': {
            'id': nota.cliente_id
        },
        'items': item_list
    }


def save_nota(nota_dict):
    return _save_documento(
        NVenta,
        NItemVenta,
        content_dict=nota_dict)


def save_factura(fact_dict):
    return _save_documento(NOrdenDespacho,
                           NItemDespacho,
                           content_dict=fact_dict)


def _save_documento(header_cls, item_cls, content_dict):
    items = content_dict['items']
    other_attr = {x: content_dict[x] for x in content_dict if x != 'items'}
    other_attr['cliente_id'] = other_attr['cliente']['id']
    del other_attr['cliente']

    session = new_session()
    header = header_cls(**other_attr)
    session.add(header)
    for num, x in enumerate(items):
        item = item_cls(
            header=header,
            num=num,
            **x
        )
        session.add(item)
    session.commit()
    return header.id




