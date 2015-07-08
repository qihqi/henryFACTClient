from henry.base.schema import *
from henry.config import sessionmanager


def main():
    with sessionmanager as session:
        for s in session.query(NPriceList).filter(
                NPriceList.multiplicador > 1):
            bid = s.almacen_id
            if bid == 3:
                bid == 1
            if s.prod_id[-1] == '+':
                upi = session.query(NContenido.id).filter_by(bodega_id=bid, prod_id=s.prod_id[:-1]).first()
                if upi is None:
                    c = NContenido(
                        prod_id=s.prod_id[:-1],
                        bodega_id=bid,
                        precio=Decimal(s.precio1)/100,
                        precio2=Decimal(s.precio2)/100,
                        cant=0,
                        cant_mayorista=s.cant_mayorista
                        )
                    session.add(c)
                    session.flush()
                    s.upi = c.id
                else:
                    s.upi = upi[0]


main()
