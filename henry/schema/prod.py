from sqlalchemy import (Column, Integer, String,
                        ForeignKey, Boolean, Numeric, Index)
from sqlalchemy.orm import relationship, backref
from henry.schema.base import Base


class NItemGroup(Base):
    '''What will replace NProducto'''
    __tablename__ = 'item_groups'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    prod_id = Column(String(20), index=True)
    name = Column(String(100))
    desc = Column(String(200))
    base_unit = Column(String(20))
    base_price_usd = Column(Numeric(11, 4))


class NItem(Base):
    __tablename__ = 'items'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    itemgroupid = Column(Integer, ForeignKey(NItemGroup.uid))
    prod_id = Column(String(20), index=True)
    multiplier = Column(Numeric(11, 3))
    unit = Column(String(20))


# TODO deprecate
class NCategory(Base):
    __tablename__ = 'categorias'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100))


class NBodega(Base):
    __tablename__ = 'bodegas'
    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100))
    nivel = Column(Integer)


class NProducto(Base):
    __tablename__ = 'productos'
    codigo = Column(String(20), primary_key=True)
    codigo_barra = Column(Integer)
    nombre = Column(String(200))
    categoria_id = Column(Integer)
    contenidos = relationship('NContenido', backref=backref('producto'))


class NStore(Base):
    __tablename__ = 'almacenes'
    almacen_id = Column('almacen_id', Integer,
                        primary_key=True, autoincrement=True)
    ruc = Column(String(20))
    nombre = Column(String(20))
    bodega_id = Column(Integer)


class NContenido(Base):
    __tablename__ = 'contenido_de_bodegas'
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    bodega_id = Column(Integer)
    prod_id = Column(String(20), ForeignKey('productos.codigo'))
    cant = Column(Numeric(23, 3))
    precio = Column(Numeric(20, 2))
    precio2 = Column(Numeric(20, 2))
    cant_mayorista = Column(Integer)
    inactivo = Column(Boolean)


class NPriceList(Base):
    __tablename__ = 'lista_de_precios'
    pid = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100))  # display name
    almacen_id = Column(Integer)
    prod_id = Column(String(20))
    # Using int for money as in number of cents.
    precio1 = Column(Integer)
    precio2 = Column(Integer)
    cant_mayorista = Column(Integer)
    upi = Column(Integer)
    unidad = Column(String(20))
    multiplicador = Column(Numeric(11, 3))

Index('ix_lista_de_precio_2', NPriceList.almacen_id, NPriceList.prod_id)


class NProdTag(Base):
    __tablename__ = 'tags'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    tag = Column(String(30), index=True)
    prod_id = Column(String(20), index=True)
