from sqlalchemy import Column, Date, Integer, String, ForeignKey, Numeric, DateTime, Index, Boolean
from sqlalchemy.orm import relationship, backref
from henry.schema.base import Base
from henry.schema.inv import NNota


class NAccountStat(Base):
    __tablename__ = 'entrega_de_cuenta'
    date = Column(Date, primary_key=True)
    total_spend = Column(Integer)
    turned_cash = Column(Integer)
    deposit = Column(Integer)
    diff = Column(Integer)
    created_by = Column(String(20))
    revised_by = Column(String(20))


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
    deposit_account_id = Column('depositado_en_id',
                                Integer, ForeignKey(NDepositAccount.uid))
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


class SpentType:
    LOCAL = 'local'
    LOCALN = 'n'  # local pero doesn't go into daily account
    FOREIGN = 'extrangero'


class NSpent(Base):
    __tablename__ = 'gastos'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    seller = Column('provedor', String(50))
    seller_ruc = Column('ruc_provedor', String(20))
    invnumber = Column('no_factura', String(50))
    invdate = Column('fecha_factura', Date)
    inputdate = Column('fecha_ingreso', DateTime)
    desc = Column(String(100))
    total = Column(Integer)
    paid_from_cashier = Column('pagado_de_caja', Integer)
    tax = Column(Integer)
    retension = Column(Integer)
    spent_type = Column(String(10))
    imgreceipt = Column(String(100))


class ObjType:
    INV = 'notas'
    TRANS = 'transfer'
    CHECK = 'cheque'
    PROD = 'prod'
    TODO = 'todo'
    ACCOUNT = 'acct'


class NComment(Base):
    __tablename__ = 'comentarios'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    objtype = Column(String(20))
    objid = Column(String(20))
    timestamp = Column(DateTime)
    user_id = Column(String(10))
    comment = Column(String(200))

Index('ix_comment_2', NComment.objtype, NComment.objid)


class NImage(Base):
    __tablename__ = 'images'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    objtype = Column(String(20))
    objid = Column(String(20))
    imgtag = Column(String(20))
    path = Column(String(100))

Index('ix_image_2', NImage.objtype, NImage.objid)

class NTodo(Base):
    __tablename__ = 'todos'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    objtype = Column(String(20))
    objid = Column(String(20))
    msg = Column(String(100))
    status = Column(String(20))
    due_date = Column(DateTime)
    creation_date = Column(DateTime)

Index('ix_todo_2', NImage.objtype, NImage.objid)


class NAccountTransaction(Base):
    __tablename__ = 'account_transaction'
    uid = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, index=True)
    desc = Column(String(100))
    type = Column(String(20))
    value = Column(Numeric(15, 4))

    deleted = Column(Boolean)
    input_timestamp = Column(DateTime)
    last_modified = Column(DateTime)

