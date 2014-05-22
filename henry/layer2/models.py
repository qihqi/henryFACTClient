import decimal
import itertools
import json
import datetime
from henry.config import new_session
from henry.layer1 import api
from henry.layer1.schema import NVenta, NItemVenta


class ModelEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'serialize'):
            return obj.serialize()
        if isinstance(obj, decimal.Decimal):
            return str(obj)
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
        self.codigo = cont.codigo.decode('latin1')
        self.nombre = cont.nombre.decode('latin1')
        self.precio1 = cont.precio
        self.precio2 = cont.precio2
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
            prod.precio1,
            prod.precio2,
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
        self.vendedor_id = None

    def merge_from_db(self, metadata, rows):
        self.id = metadata.id
        self.cliente = metadata.cliente_id
        self.bodega_id = metadata.bodega_id
        self.items = [(r.cantidad, Producto().merge_from_cont(r), r.nuevo_precio)
                      for r in rows]
        return self

    @classmethod
    def get(cls, venta_id):
        metadata = api.get_nota_de_venta_by_id(venta_id)
        rows = api.get_items_de_venta_by_id(venta_id, metadata.bodega_id)
        return cls().merge_from_db(metadata, rows)

    @staticmethod
    def save(venta):
        header = NVenta(id=venta.id,
                        vendedor_id=venta.vendedor_id,
                        cliente_id=venta.cliente,
                        fecha=datetime.date.today(),
                        bodega_id=venta.bodega_id,
                        )
        session = new_session()
        session.add(header)
        for num, (cant, producto, nuevo_p) in enumerate(venta.items):
            item = NItemVenta(header=header,
                              num=num,
                              producto_id=producto,
                              cantidad=cant,
                              nuevo_precio=nuevo_p)
            session.add(item)
        session.commit()
        return venta








