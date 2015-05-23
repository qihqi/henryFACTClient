from henry.layer1.schema import NProducto, NContenido, NPriceList, NTransform
from henry.config import sessionmanager


def get_all_contenidos(session):
    return session.query(
            NProducto.codigo,
            NProducto.nombre,
            NContenido.precio,
            NContenido.precio2,
            NContenido.bodega_id,
            NContenido.cant_mayorista,
            NContenido.id).filter(
                    NProducto.codigo == NContenido.prod_id)

def get_reglas(session, prod_id):
    return session.query(NTransform.origin_id,
            NTransform.dest_id,
            NTransform.multiplier).filter_by(origin_id=prod_id).first()



def make_lista_precio(item, unidad='unidad', multiplicador=1):
    return NPriceList(
            nombre=item.nombre,
            almacen_id=item.bodega_id,
            prod_id=item.codigo,
            precio1=int(item.precio*100),
            precio2=int(item.precio2*100),
            cant_mayorista=item.cant_mayorista,
            upi=item.id,
            unidad='unidad',
            multiplicador=1)

def get_contenido_id(session, prod_id, bodega_id):
    return session.query(NContenido.id).filter_by(
            prod_id=prod_id, bodega_id=bodega_id).first().id

def main():
    try:
        counter = 0
        last_id = None
        with sessionmanager as session:
            for item in get_all_contenidos(session):
                last_id = item.id
                new_item = make_lista_precio(item)
                regla = get_reglas(session, item.codigo)
                if regla is not None:
                    new_item.upi = get_contenido_id(session, regla.dest_id, item.bodega_id)
                    new_item.multiplicador = regla.multiplier
                    new_item.unidad = 'paquete grande'
                session.add(new_item)
                counter += 1
                if counter % 100 == 0:
                    print 'processed ', counter
    finally:
        print 'total processed', counter
        print 'last id', last_id


if __name__ == '__main__':
    main()


