from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.schema import Index
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


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
    venta_cod_id = Column('venta_cod_id', Integer, ForeignKey('notas_de_venta.id'))
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
    desp_cod_id = Column('desp_cod_id', Integer, ForeignKey('ordenes_de_despacho.id'))
    num = Column('num', Integer)
    producto_id = Column('producto_id', String(20))
    cantidad = Column('cantidad', Numeric(23, 3))
    precio = Column('precio', Numeric(20, 2))
    precio_modificado = Column('precio_modificado', Boolean)


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


class NIngreso(Base):
    __tablename__ = 'ingresos'
    id = Column(Integer, primary_key=True)
    fecha = Column(Date)
    usuario = Column(String(50))
    bodega = Column(Integer)
    bodega_desde = Column(Integer)
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


class NUsuario(Base):
    __tablename__ = 'usuarios'
    username = Column(String(50), primary_key=True)
    password = Column(String(200))
    level = Column('nivel', Integer)
    is_staff = Column(Boolean)
    last_factura = Column(Integer)
    bodega_factura_id = Column(Integer)


# ###########################################################3
# below are stuff that are not in prod yet

class NStore(Base):
    __tablename__ = 'almacenes'
    almacen_id = Column(Integer, primary_key=True, autoincrement=True)
    ruc = Column(String(20))
    nombre = Column(String(20))
    bodega_id = Column(Integer, ForeignKey('bodegas.id'))
    bodega = relationship('NBodega')


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


class NNota(Base):
    __tablename__ = 'notas'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, index=True)
    status = Column(String(10))

    # this pair should be unique
    codigo = Column(String(20))
    almacen_id = Column(Integer, ForeignKey(NStore.almacen_id))

    client_id = Column(String(20))
    user_id = Column(String(20))
    paid = Column(Boolean)
    paid_amount = Column(Integer)
    payment_format = Column(String(20))

    subtotal = Column(Integer)
    total = Column(Integer)
    tax = Column(Integer)
    discount = Column(Integer)
    tax_percent = Column(Integer)
    discount_percent = Column(Integer)

    bodega_id = Column(Integer, ForeignKey(NBodega.id))
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
    upi = Column(Integer, ForeignKey(NContenido.id))
    unidad = Column(String(20))
    multiplicador = Column(Integer)


Index('ix_lista_de_precio_2', NPriceList.almacen_id, NPriceList.prod_id)


class NDjangoSession(Base):
    __tablename__ = 'django_session'
    session_key = Column(String(40), primary_key=True)
    session_data = Column(Text)
    expire_date = Column(DateTime)
