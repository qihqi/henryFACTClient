import sys
import json
import unittest
import time

import requests

HUGE_REQUEST_NOTA = '''
{
    "items": [
        {
            "cant": 8000,
            "prod": {
                "codigo": "HCX50M",
                "nombre": "HILO CUERO 2mm PQTE",
                "precio1": 813,
                "precio2": 650,
                "threshold": 3
            }
        },
        {
            "cant": 20000,
            "prod": {
                "codigo": "COR2CMXT",
                "nombre": "CORDON 2mm X ROLLO",
                "precio1": 500,
                "precio2": 400,
                "threshold": 1
            }
        },
        {
            "cant": 20000,
            "prod": {
                "codigo": "COR3CXR",
                "nombre": "CORDON 3mm x ROLLO",
                "precio1": 480,
                "precio2": 480,
                "threshold": 0
            }
        },
        {
            "cant": 8000,
            "prod": {
                "codigo": "REATXR",
                "nombre": "REATA x ROLLO",
                "precio1": 1200,
                "precio2": 960,
                "threshold": 6
            }
        },
        {
            "cant": 14000,
            "prod": {
                "codigo": "SEPMEAF",
                "nombre": "SEP METALICO A FDA/GDE",
                "precio1": 1856,
                "precio2": 1485,
                "threshold": 3
            }
        },
        {
            "cant": 15000,
            "prod": {
                "codigo": "PJAP6",
                "nombre": "PERLA JAPONESA 0.6",
                "precio1": 81,
                "precio2": 65,
                "threshold": 6
            }
        },
        {
            "cant": 30000,
            "prod": {
                "codigo": "PJAP8",
                "nombre": "PERLA JAPONESA 0.8",
                "precio1": 94,
                "precio2": 75,
                "threshold": 6
            }
        },
        {
            "cant": 15000,
            "prod": {
                "codigo": "PJAP10",
                "nombre": "PERLA JAPONESA # 10",
                "precio1": 138,
                "precio2": 110,
                "threshold": 6
            }
        },
        {
            "cant": 10000,
            "prod": {
                "codigo": "PJAP12",
                "nombre": "PERLA JAPONESA # 12",
                "precio1": 169,
                "precio2": 135,
                "threshold": 6
            }
        },
        {
            "cant": 5000,
            "prod": {
                "codigo": "TAPLASF",
                "nombre": "TAPA ARETE PLAST F/G",
                "precio1": 240,
                "precio2": 200,
                "threshold": 3
            }
        },
        {
            "cant": 48000,
            "prod": {
                "codigo": "PINMUL",
                "nombre": "PINZA MULTIUSO",
                "precio1": 225,
                "precio2": 180,
                "threshold": 6
            }
        },
        {
            "cant": 48000,
            "prod": {
                "codigo": "PINFPP",
                "nombre": "PINZA FINA PUNTA PLANA",
                "precio1": 225,
                "precio2": 180,
                "threshold": 6
            }
        },
        {
            "cant": 1000,
            "prod": {
                "codigo": "TTCBXPT",
                "nombre": "TIRA TREN.C/BRILLO x PTQ",
                "precio1": 5625,
                "precio2": 4500,
                "threshold": 3
            }
        },
        {
            "cant": 200000,
            "prod": {
                "codigo": "TPP",
                "nombre": "TERMINAL DE PULSERA PEQ",
                "precio1": 38,
                "precio2": 30,
                "threshold": 6
            }
        },
        {
            "cant": 2000,
            "prod": {
                "codigo": "DIAD2N",
                "nombre": "DIADEMA NIQUEL 2cmx12",
                "precio1": 338,
                "precio2": 270,
                "threshold": 3
            }
        },
        {
            "cant": 2000,
            "prod": {
                "codigo": "SEPMEAF",
                "nombre": "SEP METALICO A FDA/GDE",
                "precio1": 1856,
                "precio2": 1485,
                "threshold": 3
            }
        },
        {
            "cant": 1000,
            "prod": {
                "codigo": "ATCHPF",
                "nombre": "ATACHE PEGABLES F/G",
                "precio1": 1200,
                "precio2": 1000,
                "threshold": 3
            }
        }
    ],
    "meta": {
        "almacen_id": 1,
        "bodega_id": 1,
        "client": {
            "apellidos": "GOMEZ AGUIRRE",
            "ciudad": "QUITO HAGA Y VENDA BISUTERIA",
            "codigo": "1703215549001",
            "direccion": " NACIONES UNIDAS Y JAPON C.C.N.U. LOCAL MZ-6 ",
            "nombres": "ADRIANA",
            "telefono": " 022449153-2641831-2446395-0984258949-0984258947",
            "tipo": "B"
        },
        "codigo": "111111111",
        "descuento_global_porciento": 0,
        "discount": 20311,
        "iva": 10894,
        "iva_porciento": 12,
        "subtotal": 111096,
        "total": 101679,
        "user": "yu"
    }
}
'''


class PerformanceTest(unittest.TestCase):

    def setUp(self):
        #self.addr = '192.168.0.23'
        self.addr = 'localhost:8080'
        self.url_base = 'http://%s/api' % self.addr
        self._url = 'http://%s/api/producto' % self.addr

    def test_producto(self):
        productos = ['123', '1234']
        start = time.time()
        for p in productos:
            url = self.url_base + '/alm/{}/producto/{}'.format(1, p)
            r = requests.get(url)
            print >>sys.stderr, r.text
            url = self.url_base + '/alm/{}/producto/{}'.format(2, p)
            r = requests.get(url)
            print >>sys.stderr, r.text
        end = time.time()
        print 'producto ', end - start

    def test_search_producto(self):
        start = time.time()
        r = requests.get(self._url, params={'prefijo': 'A', 'bodega_id': 1})
        print >>sys.stderr, r.text
        end = time.time()
        print 'search producto ', end - start

    def test_nota(self):
        url = self.url_base + '/nota'
        content = HUGE_REQUEST_NOTA
        assert len(content) > 0
        start = time.time()
        r = requests.post(url, data=content)
        print >>sys.stderr, r.text
        end = time.time()
        print 'post factura ', end - start

    def test_pedido(self):
        url = self.url_base + '/pedido'
        content = HUGE_REQUEST_NOTA
        start = time.time()
        r = requests.post(url, data=content)
        print >>sys.stderr, r.text
        end = time.time()
        print 'post pedido', end - start

    def test_get_cliente(self):
        url = self.url_base + '/cliente/NA'
        r = requests.get(url)
        print 'cliente ', r.text
        # r = requests.get(url, params={'prefijo': 'A'})
        #print 'cliente ', r.text

    def test_crear_ingreso(self):
        ing = {
            'meta': {
                'origin': 1,
                'dest': 2,
                'trans_type': 'TRANSFER',
                'user': 'yu',
            },
            'items': [
                {'prod': {'codigo': '123', 'nombre': 'prueba'}, 'cant': '1'},
                {'prod': {'codigo': '12', 'nombre': 'prueba'}, 'cant': '2'}
            ]
        }

        url = self.url_base + '/ingreso'
        r = requests.post(url, data=json.dumps(ing))
        print 'test ingreso ', r.content


if __name__ == '__main__':
    unittest.main()

