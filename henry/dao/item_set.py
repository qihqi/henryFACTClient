from henry.helpers.serialization import SerializableMixin
from henry.layer2.productos import Product


class Status:
    NEW = 'NUEVO'
    COMITTED = 'POSTEADO'
    DELETED = 'ELIMINADO'

    names = (NEW,
             COMITTED,
             DELETED)


class Item(SerializableMixin):
    _name = ('prod', 'cant')

    def __init__(self, prod=None, cant=None):
        self.prod = prod
        self.cant = cant

    @classmethod
    def deserialize(cls, the_dict):
        prod = Product.deserialize(the_dict['prod'])
        cant = the_dict['cant']
        return cls(prod, cant)


class MetaItemSet(SerializableMixin):
    _name = ('meta', 'items')

    def __init__(self, meta=None, items=None):
        self.meta = meta
        self.items = list(items)

    @classmethod
    def deserialize(cls, the_dict):
        raise NotImplementedError(
            'MetaItemSet cannot be deserialized. We don\'t know'
            'the correct type of meta')
