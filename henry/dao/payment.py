from henry.base.schema import NPayment, NCheck, NDeposit, NBank, NDepositAccount
from henry.base.serialization import SerializableMixin


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
    )

    def __init__(self, **kwargs):
        self.merge_from(kwargs)

    @classmethod
    def from_db_instance(cls, dbobj):
        new = cls()
        new.merge_from(dbobj)
        new.merge_from(dbobj.payment)
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
        new.merge_from(dbobj)
        new.merge_from(dbobj.payment)
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

    def save_check(self, check):
        npayment = _extract_payment(check)
        npayment.type = 'CHEQUE'
        ncheck = NCheck(
            bank=check.bank,
            accountno=check.accountno,
            checkno=check.checkno,
            holder=check.holder,
            checkdate=check.checkdate,
            deposit_account=check.deposit_account,
            status='NUEVO',
        )
        ncheck.payment = npayment
        self.sm.session.add(ncheck)
        self.sm.session.flush()
        return ncheck.uid

    def save_deposit(self, deposit):
        npayment = _extract_payment(deposit)
        npayment.type = 'CHEQUE'
        ndeposit = NDeposit(
            account=deposit.account,
            status='NUEVO',
        )
        ndeposit.payment = npayment
        self.sm.session.add(npayment)
        self.sm.session.flush()
        return ndeposit.uid

    def _get_doc(self, uid, dbclazz, objclazz):
        ndoc = self.sm.session.query(dbclazz).filter_by(uid=uid).first()
        if ndoc is None:
            return None
        return objclazz.from_db_instance(ndoc)

    def get_check(self, uid):
        return self._get_doc(uid, NCheck, Check)

    def list_checks(self, paymentdate=None, checkdate=None):
        query = self.sm.session.query(NCheck).join(NPayment)
        if paymentdate is not None:
            query.filter(NPayment.date == paymentdate)
        if checkdate is not None:
            query.filter(NCheck.checkdate == checkdate)
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
