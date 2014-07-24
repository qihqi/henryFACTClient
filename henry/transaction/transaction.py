__author__ = 'han'


class Transaction(object):

    def __init__(self, metadata, items):
        self.metadata = metadata
        self._items = items
        self.sign = 1

    @property
    def items(self):
        for cant, item in self._items:
            yield self.sign * cant, item

    def inverse(self):
        self.sign *= -1
        return self


class InventoryManager(object):

    def commit(self, transaccion):
        pass

    def create(self, transaccion):
        pass

    def delete(self, transaccion):
        pass

