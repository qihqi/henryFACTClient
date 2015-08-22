from sqlalchemy import Column, Integer, DateTime, String, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship, backref
from henry.schema.base import Base

__author__ = 'han'


class NInventoryRevision(Base):
    __tablename__ = 'revisiones_de_inventario'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    bodega_id = Column(Integer)
    timestamp = Column(DateTime, index=True)
    created_by = Column(String(20))
    status = Column(String(10))
    items = relationship('NInventoryRevisionItem', backref=backref('revision'))


class NInventoryRevisionItem(Base):
    __tablename__ = 'items_de_revisiones'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    revision_id = Column(Integer, ForeignKey(NInventoryRevision.uid))
    prod_id = Column(String(20), index=True)
    inv_cant = Column(Numeric(20, 3))
    real_cant = Column(Numeric(20, 3))


class NTransferencia(Base):
    __tablename__ = 'transferencias'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    status = Column(String(10))

    origin = Column(Integer)
    dest = Column(Integer)

    trans_type = Column(String(10))
    ref = Column(String(100))

    # unix filepath where the items is stored
    items_location = Column(String(200))


class NProdTag(Base):
    __tablename__ = 'tags'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    tag = Column(String(30), index=True)
    prod_id = Column(String(20), index=True)


class NItemGroup(Base):
    __tablename__ = 'item_groups'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    string_id = Column(String(20), index=True)
    name = Column(String(100))
    desc = Column(String(200))
    base_unit = Column(String(20))
    base_price_usd = Column(Numeric(11, 4))


class NItem(Base):
    __tablename__ = 'items'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    itemgroupid = Column(Integer, ForeignKey(NItemGroup))
    prod_id = Column(String(20), index=True)
    multiplier = Column(Numeric(11, 3))
    unit = Column(String(20))


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


class NContenido(Base):
    __tablename__ = 'contenido_de_bodegas'
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    bodega_id = Column(Integer)
    prod_id = Column(String(20), ForeignKey('productos.codigo'))
    cant = Column(Numeric(23, 3))
    precio = Column(Numeric(20, 2))
    precio2 = Column(Numeric(20, 2))
    cant_mayorista = Column(Integer)
    pricelist = relationship('NPriceList', backref=backref('cantidad'))
    inactivo = Column(Boolean)