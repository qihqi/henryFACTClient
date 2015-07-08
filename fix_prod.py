from henry.config import sessionmanager
from henry.base.schema import *

def main():
    with sessionmanager as session:
        for x in session.query(NContenido).filter(
                NContenido.prod_id.in_(['aechp50'])):
            p = NPriceList(
                prod_id=x.prod_id, 
                nombre=x.producto.nombre,
                almacen_id=x.bodega_id,
                precio1=int(x.precio * 100),
                precio2=int(x.precio2 * 100),
                cant_mayorista=int(x.cant_mayorista* 1000),
            )
            session.add(p)
    print 'fin'
                
main()
