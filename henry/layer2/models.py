from henry.layer1 import api

def identity(x):
    return x

class SerializableMixin(object):
    def serialize(self):
        def _s(name):
            attr = getattr(self, name)
            return getattr(attr, 'serialize', identity)(attr)
        result_map = {
            name: _s(name) for name in self._name
        }
        print result_map
        return result_map


class Producto(SerializableMixin):
    _name = ['nombre',
             'precio1',
             'precio2',
             'codigo',
             'threshold']

    def __init__(self, cont):
        self.codigo = cont.prod_id.decode('latin1')
        self.nombre = cont.producto.nombre.decode('latin1')
        self.precio1 = int(cont.precio * 100)
        self.precio2 = int(cont.precio * 100)
        self.threshold = cont.cant_mayorista

    @classmethod
    def get(cls, prod_id, bodega_id):
        contenido = api.get_product_by_id(prod_id, bodega_id)
        if contenido:
            return Producto(contenido)
        return None
