import unittest
from henry.dao import Transferencia, TransMetadata, Item, Product
from henry.externalapi import ExternalApi


class ExternalTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = ExternalApi('http://localhost:8080/api', 'ingreso', 'yu', 'yu')

    def test_trans(self):
        ing = Transferencia(
            meta=TransMetadata(**{
                'origin': 1,
                'dest': 2,
                'trans_type': 'TRANSFER',
                'user': 'yu',
            }),
            items=[
                Item(Product(**{'codigo': '123', 'nombre': 'prueba'}), 1),
                Item(Product(**{'codigo': '12', 'nombre': 'prueba'}), 2)
            ]
        )
        doc = self.api.save(ing)
        print doc.meta.uid


if __name__ == '__main__':
    unittest.main()
