import json
import unittest
import time

import requests


class EndToEndTest(unittest.TestCase):

    def setUp(self):
        self.url_base = 'http://localhost:8080/api'
        self._url = 'http://localhost:8080/api/producto'

    
    def test_end_to_end(self):
        # search for a product
        url = self.url_base + '/alm/1/producto' 
        r = requests.get(url, params={'prefijo': 'A'})
        content = r.json()
        
        p1 = content[0]
        p2 = content[1]
        p3 = content[2]

        url = self.url_base + '/cliente'
        clients = requests.get(url, params={'prefijo': 'N'}).json()
        client = clients[0]
        print 'clientes son', clients


        content = { 
            'meta': {
                'client_id': client['codigo'],
                'total': 123,
                'subtotal': 123,
                'tax' : '1.23',
            },
            'items': [
              (x['codigo'], 1, x['nombre'], x['precio1']) for x in (p1, p2, p3)
              ]
        }

        nota_url = self.url_base + '/nota'
        r = requests.post(nota_url, data=json.dumps(content))
        codigo = r.json()['codigo']
        print 'codigo es', codigo
        
        #get the nota back
        new_nota = requests.get(nota_url + '/' + str(codigo))
        print new_nota.json()

        

if __name__ == '__main__':
    unittest.main()
