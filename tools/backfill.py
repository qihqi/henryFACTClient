from decimal import Decimal
from henry.schema.inventory import NProducto, NContenido
from henry.schema.core import NPriceList
from henry.schema.legacy import NTransform
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
                         NTransform.multiplier,
                         NProducto.nombre).filter(
                             NTransform.dest_id == NProducto.codigo).filter_by(
                             origin_id=prod_id).first()


def make_lista_precio(item, unidad='unidad', multiplicador=1):
    return NPriceList(
        nombre=item.nombre,
        almacen_id=item.bodega_id,
        prod_id=item.codigo,
        precio1=int(item.precio * 100),
        precio2=int(item.precio2 * 100),
        cant_mayorista=item.cant_mayorista,
        upi=item.id,
        unidad='unidad',
        multiplicador=1)


def main():
    counter = 0
    last_id = None
    created = set()
    try:
        with sessionmanager as session:
            for item in get_all_contenidos(session):
                last_id = item.id
                if item.precio == 0:
                    continue
                new_item = make_lista_precio(item)
                regla = get_reglas(session, item.codigo)
                if regla is not None:
                    if regla.multiplier <= 12:
                        new_item.prod_id = regla.dest_id + '+'
                        new_item.multiplicador = regla.multiplier
                        new_item.unidad = 'paquete grande'
                    else:
                        if item.bodega_id == 1:
                            continue
                        new_item.prod_id = regla.dest_id
                        new_item.nombre = regla.nombre
                        new_item.precio1 = int(new_item.precio1 / regla.multiplier + Decimal('0.5'))
                        new_item.precio2 = int(new_item.precio2 / regla.multiplier + Decimal('0.5'))
                        if new_item.prod_id == 'HILCTP':
                            print 'precio original', item.precio, new_item.precio1

                #if (new_item.almacen_id, new_item.prod_id) in created:
                #    print (new_item.almacen_id, new_item.prod_id), 'alreaady exist'
                #else:
                counter += 1
                session.add(new_item)
                created.add((new_item.almacen_id, new_item.prod_id))
                
                if counter % 100 == 0:
                    print 'processed ', counter
    finally:
        print 'total processed', counter
        print 'last id', last_id


if __name__ == '__main__':
    main()
