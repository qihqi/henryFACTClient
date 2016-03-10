from henry.config import sessionmanager
from henry.schema.core import NPriceList
from henry.inventory.schema import NContenido


def main():
    with sessionmanager as session:
        bad_cont = list(session.query(NContenido).filter_by(bodega_id=3))
        good_cont = {}
        for c in bad_cont:
            good = session.query(NContenido).filter_by(bodega_id=1, prod_id=c.prod_id).first()
            if good is None:
                print c.prod_id
                continue
            assert good is not None, c.prod_id
            prices = session.query(NPriceList).filter(
                    NPriceList.almacen_id==3, 
                    NPriceList.prod_id.in_((c.prod_id, c.prod_id+'+')))
            for p in prices:
                p.upi = good.id
            good.cant += c.cant
            c.cant = 0
            print 'fixed {}'.format(c.prod_id)
main()
            

        
