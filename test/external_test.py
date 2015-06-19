import unittest
from henry.dao import Transferencia, TransMetadata, Item, Product
from henry.externalapi import ExternalApi


class ExternalTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = ExternalApi('http://186.68.43.214/api/', 'ingreso', 'yu', 'yu')

    def test_trans(self):
        ing = Transferencia(
            meta=TransMetadata(**{
                'dest': 1,
                'trans_type': 'INGRESO',
                'user': 'yu',
            }),
            items=[
                Item(Product(**{'codigo': '123', 'nombre': 'prueba'}), 1),
                #Item(Product(**{'codigo': '12', 'nombre': 'prueba'}), 2)
            ]
        )
        doc = self.api.save(ing)
        self.assertTrue(doc is not None)
        print doc.meta.ref


if __name__ == '__main__':
    unittest.main()
