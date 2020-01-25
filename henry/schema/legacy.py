from sqlalchemy import (Column, Integer, String, Date, ForeignKey,
                        Numeric, Boolean, Text, DateTime)
from sqlalchemy.orm import relationship, backref
from henry.schema.base import Base


__author__ = 'han'


class NVenta(Base):
    __tablename__ = 'notas_de_venta'
    id = Column('id', Integer, primary_key=True)
    vendedor_id = Column('vendedor_id', String(50))
    cliente_id = Column('cliente_id', String(20))
    fecha = Column('fecha', Date)
    bodega_id = Column('bodega_id', Integer)
    items = relationship('NItemVenta', backref=backref('header'))


class NItemVenta(Base):
    __tablename__ = 'items_de_venta'
    id = Column('id', Integer, primary_key=True)
    venta_cod_id = Column('venta_cod_id', Integer,
                          ForeignKey('notas_de_venta.id'))
    num = Column('num', Integer)
    producto_id = Column('producto_id', String(20))
    cantidad = Column('cantidad', Numeric(23, 3))
    nuevo_precio = Column('nuevo_precio', Numeric(20, 2))


class NOrdenDespacho(Base):
    __tablename__ = 'ordenes_de_despacho'
    id = Column('id', Integer, primary_key=True)
    codigo = Column('codigo', Integer)
    vendedor_id = Column('vendedor_id', String(50))
    cliente_id = Column('cliente_id', String(20))
    fecha = Column('fecha', Date)
    bodega_id = Column('bodega_id', Integer)
    pago = Column('pago', String(1))
    precio_modificado = Column('precio_modificado', Boolean)
    total = Column('total', Numeric(23, 3))
    eliminado = Column('eliminado', Boolean)
    items = relationship('NItemDespacho', backref=backref('header'))


class NItemDespacho(Base):
    __tablename__ = 'items_de_despacho'
    id = Column('id', Integer, primary_key=True)
    desp_cod_id = Column('desp_cod_id', Integer,
                         ForeignKey('ordenes_de_despacho.id'))
    num = Column('num', Integer)
    producto_id = Column('producto_id', String(20))
    cantidad = Column('cantidad', Numeric(23, 3))
    precio = Column('precio', Numeric(20, 2))
    precio_modificado = Column('precio_modificado', Boolean)


class NIngreso(Base):
    __tablename__ = 'ingresos'
    id = Column(Integer, primary_key=True)
    fecha = Column(Date)
    usuario = Column('usuario_id', String(50))
    bodega_id = Column(Integer)
    bodega_desde_id = Column(Integer)
    tipo = Column(String(1))
    items = relationship('NIngresoItem', backref=backref('header'))

    TIPO_INGRESO = 'I'
    TIPO_REEMPAQUE = 'R'
    TIPO_EXTERNA = 'E'
    TIPO_TRANSFERENCIA = 'T'


class NIngresoItem(Base):
    __tablename__ = 'ingreso_items'
    id = Column('id', Integer, primary_key=True)
    ref_id = Column('ingreso_cod_id', Integer, ForeignKey('ingresos.id'))
    num = Column('num', Integer)
    producto_id = Column('producto_id', String(20))
    cantidad = Column('cantidad', Numeric(23, 3))


class NTransform(Base):
    __tablename__ = 'transformas'

    origin_id = Column(String(20), primary_key=True)
    dest_id = Column(String(20))
    multiplier = Column(Numeric(10, 3))


class NDjangoSession(Base):
    __tablename__ = 'django_session'
    session_key = Column(String(40), primary_key=True)
    session_data = Column(Text)
    expire_date = Column(DateTime)


class NTodo(Base):
    __tablename__ = 'todos'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    objtype = Column(String(20))
    objid = Column(String(20))
    msg = Column(String(100))
    status = Column(String(20))
    due_date = Column(DateTime)
    creation_date = Column(DateTime)


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


class NProducto(Base):
    __tablename__ = 'productos'
    codigo = Column(String(20), primary_key=True)
    codigo_barra = Column(Integer)
    nombre = Column(String(200))
    categoria_id = Column(Integer)
    contenidos = relationship('NContenido', backref=backref('producto'))