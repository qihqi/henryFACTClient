from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from henry.config import sessionmanager, paymentapi
from henry.dao.payment import *
from henry.schema.account import NBank, NDepositAccount, NCheckOld, NCheck

oldcon = 'mysql+mysqldb://henry:no jodas@192.168.0.22/contabilidad'
oldengine = create_engine(oldcon)
oldsession = sessionmaker(bind=oldengine)()

def main():
    with sessionmanager as session:
        oldchecks = oldsession.query(NCheckOld)
        for c in oldchecks:
            exists = session.query(NCheck).filter_by(
                bank=c.bank.name).filter_by(
                accountno=c.cuenta).filter_by(checkno=c.numero).first()
            if exists is not None:
                print 'check exist', c.bank.name, c.cuenta, c.numero
                continue
            daccount = c.deposit_account.name if c.deposit_account else None
            newcheck = Check(
                bank=c.bank.name,
                accountno=c.cuenta,
                checkno=c.numero,
                holder=c.titular,
                value=int(c.value*100),
                checkdate=c.fecha,
                date=c.input_date,
                deposit_account=daccount)
            if newcheck.deposit_account is not None:
                newcheck.status = 'DEPOSITADO'
            else:
                newcheck.status = 'NUEVO'
            paymentapi.save_check(newcheck)
            print 'newcheck ', newcheck.bank

        for b in oldsession.query(NBank):
            session.add(NBank(uid=b.uid, name=b.name))

        for b in oldsession.query(NDepositAccount):
            session.add(NDepositAccount(uid=b.uid, name=b.name))
main()
