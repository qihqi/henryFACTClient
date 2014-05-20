import unittest
import time

import requests


class PerformanceTest(unittest.TestCase):

    def setUp(self):
        self._url = 'http://localhost:8080/api/producto'

    def test_producto(self):
        productos = ['123', '1234', '00000', 'antl5', 'aplxdoc']
        start = time.time()
        for p in productos:
            r = requests.get(self._url, params={'id': p, 'bodega_id': 1})
            print r.text
            r = requests.get(self._url, params={'id': p, 'bodega_id': 2})
            print r.text
        end = time.time()
        print 'performance ', end - start

    def test_search_producto(self):
        start = time.time()
        r = requests.get(self._url, params={'prefijo': 'ATACHE PLASTICO MD.', 'bodega_id': 1})
        print r.text
        end = time.time()
        print 'performance ', end - start


if __name__ == '__main__':
    unittest.main()