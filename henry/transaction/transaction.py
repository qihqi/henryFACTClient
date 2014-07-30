__author__ = 'han'

from itertools import imap
from henry.layer1.schema import NTransaction

class FileManager(object):

    def __init__(self, root):
        self.root = root

    def save_transaction(self, serializable):
        timestamp = serializable.timestamp
        target_filename = os.path.join(self.root, timestamp.isoformat())
        target_content = serializable
        if not isinstance(str, serializable):
            target_content = json.dumps(serializable)
        with open(target_filename, 'w') as f:
            f.write(serializable)
            f.write('\n')
            f.flush()
        return target_filename


class Transaction(object):

    def __init__(self, items):
        self.items = items

    def inverse(self):
        self.items = imap(lambda x: -x, self.items)


class InventoryManager(object):

    def __init__(self):
        pass


    def commit(self, transaccion):
        # get items of transacion
        # for each row
        # modify inventory count
        # mark status
        pass

    def create(self, transaccion):
        # serialize transacion
        serialized = transaccion.serialize()
        # save in fs by date?
        filename = self._create_filename(transaccion, Status.NEW)
        with open(filename, 'w') as f:
            f.write(json.dumps(serialized))
            f.flush()
        return transaccion

        pass

    def delete(self, transaccion):
        # get items of transacion
        # for each row
        # modify inventory count inversely
        # mark status
        pass

