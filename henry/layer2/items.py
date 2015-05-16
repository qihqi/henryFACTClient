import json
import os
from henry.helpers.serialization import SerializableMixin, json_dump
from henry.layer2.productos import Product


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


class ItemSetManager:

    def __init__(self, root):
        self.root = root

    # this need to support both full and partial paths
    def put_items(self, filename, item_set, override=True):
        dirname, name = os.path.split(filename)
        if not filename.startswith('/'):
            dirname = os.path.join(self.root, dirname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        fullpath = os.path.join(dirname, name)
        with open(fullpath, 'w') as f:
            for line in item_set:
                f.write(json_dump(line.serialize()))
            f.flush()
        return fullpath

    def get_items(self, filename):
        if not filename.startswith('/'):
            filename = os.path.join(self.root, filename)
        if os.path.exists(filename):
            with open(filename) as f:
                for line in f.readlines():
                    the_dict = json.loads(line)
                    yield Item.deserialize(the_dict)
