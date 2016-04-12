from datetime import datetime
import json
import os
import shutil
import unittest
from decimal import Decimal
from henry.base.fileservice import FileService
from henry.base.serialization import json_dumps
from henry.product.dao import (InventoryMovement, InventoryApi,
                               ProdItemGroup, InvMovementType)


class NewTransactionTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        test_root = '/tmp/transaction_test'
        if os.path.exists(test_root):
            shutil.rmtree(test_root)
        fileservice = FileService(test_root)
        api = InventoryApi(fileservice)
        cls.api = api

    def test_trans(self):
        inv = InventoryMovement()
        inv.from_inv_id = 1
        inv.to_inv_id = 2
        inv.quantity = Decimal(1)
        inv.itemgroup_id = 1
        inv.prod_id = 'AAAA'
        inv.timestamp = datetime(2016, 1, 1)
        inv.type = InvMovementType.SALE

        self.api.save(inv)

        trans = list(self.api.list_transactions(
            1,
            inv.timestamp.date(), inv.timestamp.date()))

        self.assertEquals(1, len(trans))
        self.assertDictEqual(
            json.loads(json_dumps(inv)),
            json.loads(json_dumps(trans[0]))
        )
        current_quantities = self.api.get_current_quantity(1)
        self.api.take_snapshot_to_date(inv.itemgroup_id, inv.timestamp.date())
        self.assertDictEqual(
            current_quantities,
            self.api.get_current_quantity(1))

        inv.timestamp = datetime(2016, 1, 2)
        self.api.save(inv)
        self.assertDictEqual({1: Decimal(-2), 2: Decimal(2)},
                             self.api.get_current_quantity(1))

if __name__ == '__main__':
    unittest.main()
