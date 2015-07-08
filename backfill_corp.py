from decimal import Decimal
from henry.base.schema import NProducto, NContenido, NPriceList, NTransform
from henry.config import sessionmanager
from sqlalchemy.orm.session import make_transient

def main():
    with sessionmanager as session:
        for x in session.query(NPriceList).filter_by(almacen_id=1):
            session.expunge(x)
            make_transient(x)
            x.pid = None
            x.almacen_id = 3
            session.add(x)
main()
