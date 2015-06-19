import datetime
import json
import unittest
import time

import requests

class Timing:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.start = time.time()
        return self
    
    def __exit__(self, *args, **kwargs):
        self.end = time.time()
        print self.name, ': ', self.end - self.start




class EndToEndTest(unittest.TestCase):

    def setUp(self):
        self.url_base = 'http://192.168.0.23/api'

    
    def test_end_to_end(self):
        #authenticate
        print 'Today is ', datetime.datetime.now().isoformat()
        url = self.url_base + '/authenticate'
        r = None
        response = None
        with Timing('authenticate'):
            r = requests.post(url, data={'username': 'yu', 'password': 'yu'})
            response = r.json()
        cookies = r.cookies
        print response
        number = response['last_factura']
        # search for a product
        url = self.url_base + '/alm/1/producto' 
        content = None
        with Timing('search producto'):
            r = requests.get(url, params={'prefijo': 'A'})
            content = r.json()
        
        p1 = content[0]
        p2 = content[1]
        p3 = content[2]

        url = self.url_base + '/cliente'
        client = None
        with Timing('Search client'):
            clients = requests.get(url, params={'prefijo': 'N'}).json()
            client = clients[0]

        content = { 
            'meta': {
                'client': client,
                'total': 123,
                'subtotal': 123,
                'tax' : '1.23',
                'user_id': 'yu',
                'codigo': str(number),
                'almacen_id': 1,
            },
            'items': [
                {'prod': x, 'cant': 10} for x in (p1, p2, p3)
                ]
        }

        nota_url = self.url_base + '/nota'
        codigo = None
        with Timing('save factura'):
            r = requests.post(nota_url, data=json.dumps(content), cookies=cookies)
            codigo = r.json()['codigo']
        print 'codigo es', codigo

        with Timing('put factura'):
            r = requests.put(self.url_base + '/nota/' + str(codigo), cookies=cookies)
            print r
        
        print '================================Test end============================================'

        

if __name__ == '__main__':
    unittest.main()
