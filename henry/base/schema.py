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
    inactivo = Column(Boolean)


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
    retension = Column(Integer)
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
    multiplicador = Column(Numeric(11, 3))


Index('ix_lista_de_precio_2', NPriceList.almacen_id, NPriceList.prod_id)


class NDjangoSession(Base):
    __tablename__ = 'django_session'
    session_key = Column(String(40), primary_key=True)
    session_data = Column(Text)
    expire_date = Column(DateTime)


class NAccountStat(Base):
    __tablename__ = 'entrega_de_cuenta'
    date = Column(Date, primary_key=True)
    total_spend = Column(Integer)
    turned_cash = Column(Integer)
    deposit = Column(Integer)
    diff = Column(Integer)
    created_by = Column(String(20))
    revised_by = Column(String(20))


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


class NBank(Base):
    __tablename__ = 'cheque_banco'
    uid = Column('id', Integer, primary_key=True, autoincrement=True)
    name = Column('nombre', String(100))


class NDepositAccount(Base):
    __tablename__ = 'cheque_cuenta'
    uid = Column('id', Integer, primary_key=True, autoincrement=True)
    name = Column('nombre', String(100))


class NCheckOld(Base):
    __tablename__ = 'cheque_cheque'
    uid = Column('id', Integer, primary_key=True, autoincrement=True)
    bank_id = Column('banco_id', Integer, ForeignKey(NBank.uid))
    bank = relationship(NBank)
    cuenta = Column(String(100))

    numero = Column(Integer)
    titular = Column(String(100))

    value = Column('valor', Numeric(20, 2))
    fecha = Column(Date)

    input_date = Column('fecha_ingreso', Date)
    por_compra = Column(String(100))
    deposit_account_id = Column('depositado_en_id', Integer, ForeignKey(NDepositAccount.uid))
    deposit_account = relationship(NDepositAccount)


class NPayment(Base):
    __tablename__ = 'pagos'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    note_id = Column(Integer, ForeignKey(NNota.id))
    client_id = Column(String(20))
    value = Column('valor', Integer)
    type = Column('tipo', String(10))
    date = Column('fecha', Date)

    nota = relationship('NNota', backref=backref('payments'))


class NCheck(Base):
    __tablename__ = 'cheques_recibidos'
    uid = Column('id', Integer, primary_key=True, autoincrement=True)
    bank = Column('banco', String(30))
    accountno = Column(String(20))
    checkno = Column('numero', Integer)
    holder = Column('titular', String(40))
    checkdate = Column('fecha_cheque', Date)

    imgcheck = Column(String(100))
    imgdeposit = Column(String(100))

    deposit_account = Column('depositado_en', String(30))
    status = Column(String(10))

    payment_id = Column(Integer, ForeignKey(NPayment.uid))
    payment = relationship(NPayment)


class NDeposit(Base):
    __tablename__ = 'depositos'
    uid = Column('id', Integer, primary_key=True, autoincrement=True)
    account = Column('cuenta', String(30))
    status = Column(String(10))
    revised_by = Column(String(10))

    payment_id = Column(Integer, ForeignKey(NPayment.uid))
    payment = relationship(NPayment)


class ObjType:
    INV = 'notas'
    TRANS = 'transfer'
    CHECK = 'cheque'


class NComment(Base):
    __tablename__ = 'comentarios'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    objtype = Column(String(20))
    objid = Column(String(20))
    timestamp = Column(DateTime)
    user_id = Column(String(10))
    comment = Column(String(200))

Index('ix_comment_2', NComment.objtype, NComment.objid)


