import json
import unittest
from henry import common


class CommonTest(unittest.TestCase):

    def test_aes(self):
        ord_str = 'hellow rodl aldlfsajfsljf sljfsl'
        x = common.aes_encrypt(ord_str.encode('utf-8'))
        y = common.aes_decrypt(x)
        self.assertEqual(y.decode('utf-8'), ord_str)

        json_dict = {
                'a' : 8,
                'b' : 8,
                'c': 'asdfsad'
                }
         
        x = common.aes_encrypt(
                json.dumps(json_dict).encode('utf-8'))
        y = common.aes_decrypt(x)
        self.assertEqual(json.loads(y.decode('utf-8')), json_dict)


if __name__ == '__main__':
    unittest.main()

