import os
from henry.layer1.serialization import SerializableMixin

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
            f.write(content)
            f.flush()
        return fullpath

    def get_items(self, filename):
        if not filename.startswith('/'):
            filename = os.path.join(self.root, filename)
        if not os.path.exists(name):
            return None
        with open(name) as f:
            return f.read()


class Item(SerializableMixin):
    _name = ('prod', 'cant')

    def __init__(self, prod, cant):
        self.prod = prod
        self.cant = cant


