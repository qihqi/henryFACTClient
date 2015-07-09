from henry.config import sessionmanager

from henry.base.schema import *

with sessionmanager as session:
    reglas = list(session.query(NTransform, NContenido).filter(
        NTransform.origin_id == NContenido.prod_id))
    for t, c in reglas:
        cant = c.cant * t.multiplier
        count = session.query(NContenido).filter_by(prod_id=t.dest_id, bodega_id=c.bodega_id).update(
                {'cant': NContenido.cant + cant})
        c.cant = 0
        c.cant_mayorista = -100
        if count == 0:
            c = NContenido(
                prod_id=t.dest_id,
                bodega_id=c.bodega_id,
                cant=cant,
                precio=100,
                precio2=100,
                cant_mayorista=-10)
            session.add(c)
            
        
