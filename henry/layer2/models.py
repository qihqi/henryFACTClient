import decimal
import itertools
import json
from henry.layer1 import api


class ModelEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'serialize'):
            return obj.serialize()
        return super(ModelEncoder, self).default(obj)


class SerializableMixin(object):
    def serialize(self):
        return {
            name: getattr(self, name) for name in self._name
        }

    def to_json(self):
        return json.dumps(self.serialize(), cls=ModelEncoder)


class Producto(SerializableMixin):
    _name = ['nombre',
             'precio1',
             'precio2',
             'codigo',
             'threshold']

    def __init__(self,
                 codigo=None,
                 nombre=None,
                 precio1=None,
                 precio2=None,
                 threshold=None):
        self.codigo = codigo
        self.nombre = nombre
        self.precio1 = precio1
        self.precio2 = precio2
        self.threshold = threshold

    def merge_from_cont(self, cont):
        self.codigo = cont.prod_id.decode('latin1')
        self.nombre = cont.producto.nombre.decode('latin1')
        self.precio1 = int(cont.precio * 100)
        self.precio2 = int(cont.precio2 * 100)
        self.threshold = cont.cant_mayorista
        return self

    @classmethod
    def get(cls, prod_id, bodega_id):
        contenido = api.get_product_by_id(prod_id, bodega_id)
        if contenido:
            return cls().merge_from_cont(contenido)
        return None

    @classmethod
    def search(cls, prefix, bodega=None):
        return itertools.imap(lambda c: cls().merge_from_cont(c),
                              api.search_product(prefix, bodega))

    @staticmethod
    def save(prod, bodega_id):
        api.create_product(
            prod.codigo,
            prod.nombre,
            decimal.Decimal(prod.precio1) / 100,
            decimal.Decimal(prod.precio2) / 100,
            bodega=bodega_id
        )
        return prod

    def __cmp__(self, other):
        return self.codigo.__cmp__(other.codigo)



class Venta(SerializableMixin):
    _name = ['cliente',
             'bodega_id',
             'id',
             'items']

    def __init__(self, cliente=None, bodega_id=None, items=None):
        self.id = None
        self.cliente = cliente
        self.bodega_id = bodega_id
        self.items = items # items is una list de tuple (cantidad, codigo)

    def merge_from_db(self, metadata, rows):
        self.id = metadata.id
        self.cliente = metadata.cliente_id
        self.items = (rows, )
        return self

    @classmethod
    def get(cls, venta_id):
        metadata = api.get_nota_de_venta_by_id(venta_id)
        rows = api.get_items_de_venta_by_id(venta_id, metadata.bodega_id)
        return cls().merge_from_db(metadata, rows)





