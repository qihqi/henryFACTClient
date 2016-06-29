from henry.inventory.schema import NContenido
from henry.schema.legacy import NTransform
from henry.config import sessionmanager

def get_all_productos(session, all_reglas):
    distinct_prod_ids = [x.origin_id for x in all_reglas]
    distinct_prod_ids.extend([x.dest_id for x in all_reglas])
    result = {}
    for x in session.query(NContenido).filter(NContenido.prod_id.in_(distinct_prod_ids)).filter_by(bodega_id=2):
        result[x.prod_id.upper()] = x
    return result


def main():
    with sessionmanager as session:
        all_reglas = list(session.query(NTransform))
        all_prod = get_all_productos(session, all_reglas)
        for x in all_reglas:
            try:
                origin = all_prod[x.origin_id.upper()]
                dest = all_prod[x.dest_id.upper()]
                print '\t'.join((
                    origin.prod_id, 
                    str(origin.precio),
                    str(x.multiplier),
                    dest.prod_id, 
                    str(dest.precio), 
                    str(origin.precio*x.multiplier)))

            except KeyError:
                print 'Key error ', x.origin_id, x.dest_id
main()
