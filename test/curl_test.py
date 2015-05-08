import json
import unittest
import time

import requests


class PerformanceTest(unittest.TestCase):

    def setUp(self):
        self.url_base = 'http://localhost:8080/api'
        self._url = 'http://localhost:8080/api/producto'

    def test_producto(self):
        productos = ['123', '1234']
        start = time.time()
        for p in productos:
            url = self.url_base + '/alm/{}/producto/{}'.format(1, p)
            r = requests.get(url)
            print r.text
            url = self.url_base + '/alm/{}/producto/{}'.format(2, p)
            r = requests.get(url)
            print r.text
        end = time.time()
        print 'producto ', end - start

    def test_search_producto(self):
        start = time.time()
        r = requests.get(self._url, params={'prefijo': 'A', 'bodega_id': 1})
        print r.text
        end = time.time()
        print 'search producto ', end - start

    def test_nota(self):
        url = self.url_base + '/nota'
        content = { 
            'meta': {
                'client_id': 'NA',
                'total': 123,
                'subtotal': 123,
                'tax' : '1.23',
            },
            'items':[
              ['A1', 1, 'A1', 0.10]
              ]
        }

        r = requests.post(url, data=json.dumps(content))
        print r.text

    def test_get_cliente(self):
        url = self.url_base + '/cliente/NA'
        r = requests.get(url)
        print 'cliente ', r.text
        # r = requests.get(url, params={'prefijo': 'A'})
        #print 'cliente ', r.text


if __name__ == '__main__':
    unittest.main()
