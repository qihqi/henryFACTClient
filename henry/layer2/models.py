
class SerializableMixin(object):
    def serialize(self):
        result_map = {
            name: getattr(self, name) for name in self._name
        }
        return result_map


class Producto(SerializableMixin):
    _name = ['nombre',
             'precio',
             'precio2',
             'codigo',
             'threshold']

    def __init__(self, cont, prod):
        self.cont = cont
        self.prod = prod

    @property
    def nombre(self):
        return self.prod.nombre

    @property
    def precio(self):
        return self.cont.precio

    @property
    def precio2(self):
        return self.cont.precio

    @property
    def codigo(self):
        return self.prod.codigo

    @property
    def threshold(self):
        return self.cont.cant_mayorista
