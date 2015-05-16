from collections import defaultdict
import unittest

from henry.layer2.productos import Product
from henry.layer2.items import ItemSetManager, Item


class ItemSetTest(unittest.TestCase):

    def setUp(self):
        self.item_manager = ItemSetManager('/tmp')


    def test_path1(self):
        s = defaultdict(Item)
        path = '/tmp/1'

        s['AAAA'] = Item(Product(
            nombre='1',
            codigo='AAAA',
            precio1=1,
            precio2=2,
            threshold=1,
            cantidad=0), 1)
        new_path = self.item_manager.put_items(path, s.values())
        self.assertEquals(new_path, path)
        items = list(self.item_manager.get_items(new_path))
        self.assertEquals(1, len(items))
        self.assertEquals('AAAA', items[0].prod.codigo)
        self.assertEquals(1, items[0].cant)


if __name__ == '__main__':
    unittest.main()
