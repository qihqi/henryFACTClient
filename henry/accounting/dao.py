import os
import uuid
from sqlalchemy import desc
from henry.base.dbapi import dbmix
from henry.base.serialization import SerializableMixin
from henry.invoice.dao import PaymentFormat

from .acct_schema import (NBank, NDepositAccount, NPayment, NCheck, NDeposit, NImage,
                          NComment, NTodo, NAccountStat, NSpent, NAccountTransaction)

Todo = dbmix(NTodo)
Comment = dbmix(NComment)
Image = dbmix(NImage)
Bank = dbmix(NBank)
DepositAccount = dbmix(NDepositAccount)
AccountStat = dbmix(NAccountStat)
Spent = dbmix(NSpent)


class Payment(SerializableMixin):
    _name = (
        'uid',
        'note_id',
        'client_id',
        'value',
        'date',
        'type',
    )

    def __init__(self, **kwargs):
        self.merge_from(kwargs)


class Check(SerializableMixin):
    _name = (
        'uid',
        'bank',
        'accountno',
        'checkno',
        'holder',
        'checkdate',
        'deposit_account',
        'status',
        'note_id',
        'client_id',
        'value',
        'date',
        'imgcheck',
        'imgdeposit',
    )

    def __init__(self, **kwargs):
        self.merge_from(kwargs)

    @classmethod
    def from_db_instance(cls, dbobj):
        new = cls()
        # this ordering is important
        new.merge_from(dbobj.payment)
        new.merge_from(dbobj)
        return new


class Deposit(SerializableMixin):
    _name = (
        'uid',
        'account',
        'status',
        'revised_by',
        'note_id',
        'client_id',
        'value',
        'date',
    )

    def __init__(self, **kwargs):
        self.merge_from(kwargs)

    @classmethod
    def from_db_instance(cls, dbobj):
        new = cls()
        new.merge_from(dbobj.payment)
        new.merge_from(dbobj)
        return new


def _extract_payment(payment):
    return NPayment(
        note_id=payment.note_id,
        client_id=payment.client_id,
        value=payment.value,
        date=payment.date,
    )



class PaymentApi:
    def __init__(self, sessionmanager):
        self.sm = sessionmanager

    def save_payment(self, payment, ptype):
        npayment = _extract_payment(payment)
        npayment.type = ptype
        if ptype == PaymentFormat.CHECK:
            dbinstance = NCheck(
                bank=payment.bank,
                accountno=payment.accountno,
                checkno=payment.checkno,
                holder=payment.holder,
                checkdate=payment.checkdate,
                deposit_account=payment.deposit_account,
                status='NUEVO',
            )
            dbinstance.payment = npayment
        elif ptype == PaymentFormat.DEPOSIT:
            dbinstance = NDeposit(
                account=payment.account,
                status='NUEVO',
            )
            dbinstance.payment = npayment
        else:
            dbinstance = npayment
        self.sm.session.add(dbinstance)
        self.sm.session.flush()
        return dbinstance.uid

    def save_check(self, check):
        return self.save_payment(check, PaymentFormat.CHECK)

    def save_deposit(self, deposit):
        return self.save_payment(deposit, PaymentFormat.DEPOSIT)

    def _get_doc(self, uid, dbclazz, objclazz):
        ndoc = self.sm.session.query(dbclazz).filter_by(uid=uid).first()
        if ndoc is None:
            return None
        return objclazz.from_db_instance(ndoc)

    def get_check(self, uid):
        return self._get_doc(uid, NCheck, Check)

    def list_payments(self, start, end):
        return map(Payment.deserialize,
                   self.sm.session.query(NPayment).filter(
                       NPayment.date >= start).filter(NPayment.date <= end))

    def list_checks(self, paymentdate=None, checkdate=None):
        query = self.sm.session.query(NCheck).join(NPayment)
        if paymentdate is not None:
            start, end = paymentdate
            query = query.filter(NPayment.date >= start, NPayment.date <= end)
        if checkdate is not None:
            start, end = checkdate
            query = query.filter(NCheck.checkdate >= start, NCheck.checkdate <= end)
        if paymentdate:
            query = query.order_by(desc(NPayment.date))
        else:
            query = query.order_by(desc(NCheck.checkdate))
        return map(Check.from_db_instance, query)

    def get_deposit(self, uid):
        return self._get_doc(uid, NDeposit, Deposit)

    def create_bank(self, name):
        self.sm.session.add(NBank(name=name))

    def get_all_banks(self):
        return self.sm.session.query(NBank)

    def create_account(self, name):
        self.sm.session.add(NDepositAccount(name=name))

    def get_all_accounts(self):
        return self.sm.session.query(NDepositAccount)


class ImageServer:
    def __init__(self, imgbasepath, dbapi, fileapi, imagewriter):
        self.imgbasepath = imgbasepath
        self.dbapi = dbapi
        self.fileapi = fileapi
        self.write_image = imagewriter

    def getimg(self, objtype, objid):
        imgs = self.dbapi.search(Image, objtype=objtype, objid=objid)

        def addpath(img):
            img.imgurl = self.get_url_path(img.path)
            return img

        return map(addpath, imgs)

    def get_url_path(self, filepath):
        if filepath is None:
            return None
        _, filename = os.path.split(filepath)
        return os.path.join(self.imgbasepath, filename)

    def saveimg(self, objtype, objid, data, replace=False):
        _, ext = os.path.splitext(data.raw_filename)
        filename = uuid.uuid1().hex + ext
        filename = self.fileapi.make_fullpath(filename)
        self.write_image(data.file, (1024, 768), filename)
        img = Image(
            objtype=objtype, objid=objid,
            path=filename)
        if replace:
            count = self.dbapi.db_session.query(NImage).filter_by(
                objtype=objtype, objid=objid).update(
                {'path': filename})
            if count == 0:
                self.dbapi.create(img)
        else:
            self.dbapi.create(img)
        return img


class AccountTransaction(dbmix(NAccountTransaction)):
    SALE = 'sales'
    SPENT = 'spents'
    CUSTOMER_PAYMENT = 'payments'
    TURNED_IN = 'turned_in'

    def serialize(self):
        result = super(AccountTransaction, self).serialize()
        if hasattr(self, 'img'):
            result['img'] = self.img
        return result

