from collections import defaultdict
from henry.config import sessionmanager
from henry.base.schema import *

def main():
    content = []
    with open('hello2.txt') as f:
        for x in f:
            d = eval(x)
            content.append((d['codigo'], d['nombre']))
    with sessionmanager as session:
        for codigo, nombre in content:
            regla = session.query(NTransform).filter_by(origin_id=codigo).first()
            if regla is None:
                print 'regla for ', codigo , 'is None'
                continue
            cont = list(session.query(NContenido).filter(
                NContenido.prod_id.in_((codigo, regla.dest_id))))
            grouped = {} 
            for c in cont:
                grouped[(c.bodega_id, c.prod_id.upper())] = c

            for bid in (1,2):
                codigo = codigo.upper()
                existing = session.query(NPriceList).filter_by(prod_id=codigo).delete()
                try:
                    c = grouped[(bid, codigo)]
                except KeyError:
                    print (bid, codigo)
                    continue
                if c.precio == 0:
                    print codigo, 'tiene 0 precio, pasando'
                price = NPriceList(
                    almacen_id=bid,
                    prod_id=regla.dest_id+'+',
                    nombre=nombre,
                    precio1=int(c.precio*100),
                    precio2=int(c.precio2*100),
                    cant_mayorista=int(c.cant_mayorista*100) if c.cant_mayorista else None,
                    upi=grouped[(bid, regla.dest_id.upper())].id,
                    multiplicador=regla.multiplier,
                    )
                session.add(price)
                if bid == 1:
                    price2 = NPriceList(
                        almacen_id=3,
                        prod_id=regla.dest_id+'+',
                        nombre=nombre,
                        precio1=int(c.precio*100),
                        precio2=int(c.precio2*100),
                        cant_mayorista=int(c.cant_mayorista*100) if c.cant_mayorista else None,
                        upi=grouped[(bid, regla.dest_id.upper())].id,
                        multiplicador=regla.multiplier,
                        )
                    session.add(price2)

main()
