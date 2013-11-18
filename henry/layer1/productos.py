from ..helpers.connection import get_database_connection
from sqlalchemy import (Table, MetaData, String, Column, Integer,
                        Numeric)
from sqlalchemy.sql import select

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

    nota_de_venta = Table('notas_de_venda', metadata,
            Column('id', Integer, primary_key=True),
            Column('vendedor_id',



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



