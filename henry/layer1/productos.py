import json
import datetime
from decimal import Decimal
from ..helpers.connection import get_database_connection
from sqlalchemy import (Table, MetaData, String, Column, Integer,
                        Numeric, Date, Boolean)
from sqlalchemy.sql import select, insert

class Schemas(object):
    metadata = MetaData()
    producto = Table('productos', metadata,
            Column('codigo', String(20), primary_key=True),
            Column('codigo_barra', Integer),
            Column('nombre', String(200)),
            Column('categoria_id', Integer))
    contenido = Table('contenido_de_bodegas', metadata,
            Column('bodega_id', Integer),
            Column('prod_id', String(20)),
            Column('cant', Numeric(23, 3)),
            Column('precio', Numeric(20, 2)),
            Column('precio2', Numeric(20, 2)),
            Column('cant_mayorista', Integer))

    nota_de_venta = Table('notas_de_venta', metadata,
            Column('id', Integer, primary_key=True),
            Column('vendedor_id', String(50)),
            Column('cliente_id', String(20)),
            Column('fecha', Date),
            Column('bodega_id', Integer))

    item_de_venta = Table('items_de_venta', metadata,
            Column('id', Integer, primary_key=True),
            Column('venta_cod_id', Integer),
            Column('num', Integer),
            Column('producto_id', String(20)),
            Column('cantidad', Numeric(23,3)),
            Column('nuevo_precio', Numeric(20, 2)))

    orden_de_despacho = Table('ordenes_de_despacho', metadata,
            Column('id', Integer, primary_key=True),
            Column('codigo', Integer),
            Column('vendedor_id', String(50)),
            Column('cliente_id', String(20)),
            Column('fecha', Date),
            Column('bodega_id', Integer),
            Column('pago', String(1)),
            Column('precio_modificado', Boolean),
            Column('total', Numeric(23,3)),
            Column('eliminado', Boolean))


    item_de_despacho = Table('items_de_despacho', metadata,
            Column('id', Integer, primary_key=True),
            Column('desp_cod_id', Integer),
            Column('num', Integer),
            Column('producto_id', String(20)),
            Column('cantidad', Numeric(23,3)),
            Column('precio', Numeric(20, 2)),
            Column('precio_modificado', Boolean))

def get_product_by_id(id, bodega_id):
    query = select([Schemas.producto, Schemas.contenido]).where(
                  (Schemas.producto.c.codigo == id) &
                  (Schemas.contenido.c.prod_id == id) &
                  (Schemas.contenido.c.bodega_id == bodega_id))

    engine = get_database_connection()
    result_set = engine.execute(query)
    result = result_set.fetchone()
    result_set.close()
    return result


def serialize_product(product_row):
    if not product_row:
        return 'None'
    return json.dumps({
        'codigo' : product_row.codigo,
        'precio' : str(product_row.precio),
        'nombre' : product_row.nombre
    })


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
            'codigo' : item.producto_id,
            'nombre' : item.nombre,
            'cantidad' : str(item.cantidad),
            'precio' : str(item.precio)}
    item_list = map(serialize_item, rows)
    return json.dumps({
        'cliente' : {
            'id' : nota.cliente_id
        },
        'items' : item_list
    })


def insert_invoice(invoice):
    invoice, rows = preprocess_input(invoice)
    engine = get_database_connection()
    with engine.begin() as connection:
        print 'invoice', invoice
        ins = Schemas.orden_de_despacho.insert()
        ins = ins.values(fecha=datetime.date.today(),
                         precio_modificado=False,
                         eliminado=False,
                         **invoice)
        print ins.parameters
        inv_id = connection.execute(ins).inserted_primary_key[0]
        ins = Schemas.item_de_despacho.insert()
        counter = 0
        for row in rows:
            ins = ins.values(
                desp_cod_id=inv_id,
                num=counter,
                **row)
            ins.compile()
            connection.execute(ins)


def preprocess_input(invoice):
    rows = invoice['rows']
    del invoice['rows']
    engine = get_database_connection()

    total = 0
    precio_modificado = False
    for r in rows:
        precio = get_product_by_id(r['producto_id'], invoice['bodega_id']).precio
        total += precio
        r['precio'] = precio
    invoice['total'] = total
    return invoice, rows






