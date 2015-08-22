from sqlalchemy import (Column, Integer, DateTime, String,
                        ForeignKey, Boolean, Numeric, Index, Date)
from henry.schema.base import Base


class NNota(Base):
    __tablename__ = 'notas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    status = Column(String(10))

    # this pair should be unique
    codigo = Column(String(20))
    almacen_id = Column()
    almacen_name = Column(String(20))
    almacen_ruc = Column(String(20))

    client_id = Column(String(20))
    user_id = Column(String(20))
    paid = Column(Boolean)
    paid_amount = Column(Integer)
    payment_format = Column(String(20))

    subtotal = Column(Integer)  # sum of items
    total = Column(Integer)  # amount of money received total = subtotal - discount + iva - retension
    tax = Column(Integer)
    retension = Column(Integer)  # (TODO) have to deprecate
    discount = Column(Integer)
    tax_percent = Column(Integer)
    discount_percent = Column(Integer)

    bodega_id = Column(Integer)
    # unix filepath where the items is stored
    items_location = Column(String(200))

Index('ix_notas_2', NNota.almacen_id, NNota.codigo)


class NPedidoTemporal(Base):
    __tablename__ = 'pedidos_temporales'
    id = Column(Integer, autoincrement=True, primary_key=True)
    client_lastname = Column(String(20), index=True)
    user = Column(String(20))
    total = Column(Integer)
    timestamp = Column(DateTime)
    status = Column(String(10))
    external_id = Column(Integer)


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


class NUsuario(Base):
    __tablename__ = 'usuarios'
    username = Column(String(50), primary_key=True)
    password = Column(String(200))
    level = Column('nivel', Integer)
    is_staff = Column(Boolean)
    last_factura = Column(Integer)
    bodega_factura_id = Column(Integer)


class NCliente(Base):
    __tablename__ = 'clientes'
    codigo = Column(String(20), primary_key=True)
    nombres = Column(String(100))
    apellidos = Column(String(100))
    direccion = Column(String(300), nullable=True)
    ciudad = Column(String(50), nullable=False)
    telefono = Column(String(50), nullable=True)
    tipo = Column(String(1))
    cliente_desde = Column(Date)


class NStore(Base):
    __tablename__ = 'almacenes'
    almacen_id = Column(Integer, primary_key=True, autoincrement=True)
    ruc = Column(String(20))
    nombre = Column(String(20))
    bodega_id = Column(Integer)
