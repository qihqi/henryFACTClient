from __future__ import print_function
from builtins import str
from builtins import object
import datetime
import json
import unittest
import time

import requests

class Timing(object):
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.start = time.time()
        return self

    def __exit__(self, *args, **kwargs):
        self.end = time.time()
        print(self.name, ': ', self.end - self.start)




class EndToEndTest(unittest.TestCase):

    def setUp(self):
       # self.url_base = 'http://192.168.0.23/api'
        #self.url_base = 'http://45.55.88.99:99/api'
        self.url_base = 'http://localhost:8080/api'


    def test_end_to_end(self):
        #authenticate
        print('Today is ', datetime.datetime.now().isoformat())
        url = self.url_base + '/authenticate'
        r = None
        response = None
        with Timing('authenticate'):
            r = requests.post(url, data={'username': 'yu', 'password': 'yu'})
            response = r.json()
            print(response)
        cookies = r.cookies
        print(r.cookies)
        print(response)
        number = response['last_factura']
        # search for a product
        url = self.url_base + '/alm/1/producto'
        content = None
        with Timing('search producto'):
            r = requests.get(url, params={'prefijo': 'h'})
            content = r.json()


        p1 = content[0]
        p2 = content[0]
        p3 = content[0]

        del p1['upi']  # test one without upi

        with Timing('get producto'):
            p3 = requests.get(url + '/' + p3['codigo']).json()

        url = self.url_base + '/cliente'
        client = None

        with Timing('Search users'):
            clients = requests.get(url, params={'prefijo': 'a'})
            client = clients.json()[0]

        with Timing('get cliente'):
            client = requests.get(url + '/na').json()

        content = {
            'items': [
                {'prod': x, 'cant': 10000} for x in (p1, p2, p3)
                ],
            'options': {
                'incrementar_codigo': True
                }
        }

        content['meta'] = {
            'client': client,
            'total': 123,
            'subtotal': sum((x['precio1'] * 10 for x in (p1, p2, p3))),
            'tax': 123,
            'user': 'yu',
            'codigo': str(number),
            'almacen_id': 1,
        }

        nota_url = self.url_base + '/nota'
        codigo = None
        with Timing('save factura'):
            r = requests.post(nota_url, data=json.dumps(content), cookies=cookies)
            codigo = r.json()['codigo']
            uid = r.json()['uid']
        print('codigo es', codigo)

        with Timing('put factura'):
            r = requests.put(self.url_base + '/nota/' + str(codigo), cookies=cookies)
            self.assertEquals(200, r.status_code)
            print(r)
        
       # at this point, NotaExtra is created.
        with dbapi.session:
            ne = dbapi.get(uid, NotaExtra)
        assert ne is not None
        assert ne.status == 'POSTEADO'

        with Timing('Get FACTura'):
            r = requests.get(nota_url + '/' + str(codigo), cookies=cookies)
            fact = r.json()
            self.assertEquals(codigo, fact['meta']['uid'])
            self.assertEquals(1, fact['meta']['almacen_id'])
            print('got factura ', fact)

        with Timing('Delete'):
            r = requests.delete(nota_url + '/' + str(codigo), cookies=cookies)
            self.assertEquals(200, r.status_code)
            print(r)

        with dbapi.session:
            ne = dbapi.get(uid, NotaExtra)
        assert ne is not None
        assert ne.status == 'ELIMINADO'




        print('================================Test end============================================')



if __name__ == '__main__':
    unittest.main()
