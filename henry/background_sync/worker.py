import json
from urllib.parse import urljoin
from decimal import Decimal

import datetime

import requests

from henry.base.serialization import json_dumps, SerializableMixin
from henry.dao.document import Status
from henry.sale_records.dao import InvMovementMeta, ItemGroupCant, InvMovementFull, Sale
from henry.inventory.dao import Transferencia, transtype_to_invtype
from henry.invoice.dao import InvMetadata, Invoice


# What actions needs to be forwarded?

# create/post/delete nota
# create/post/delete ingreso
# create client
# create product
# alter product price (changes to pricelist)
from henry.product.dao import ProdItemGroup, InvMovementType

# NOTE: this stuff is pretty new and not much in use (2020-01-25)


class WorkObject(SerializableMixin):
    CREATE = 'create'
    DELETE = 'delete'
    INV = 'inv'
    TRANS = 'trans'
    INV_TRANS = 'inv_trans'

    _name = ('objid', 'objtype', 'action', 'content')

    def __init__(self, objid=None, objtype=None, action=None, content=None):
        self.objid = objid
        self.objtype = objtype
        self.action = action
        self.content = content

    def __repr__(self):
        return 'WorkObject<objid={}, objtype={}, action={}, content={}>'.format(
            self.objid, self.objtype, self.action, self.content
        )

def doc_to_workobject(inv, action, objtype):
    obj = WorkObject()
    obj.content = inv.meta if objtype == WorkObject.INV else inv
    obj.action = action
    obj.objtype = objtype
    obj.objid = inv.meta.uid
    return obj

class ForwardRequestProcessor(object):

    def __init__(self, dbapi, root_url, auth, codename):
        self.dbapi = dbapi
        self.root_url = root_url
        self.auth = auth
        self.cookies = None
        self.codename = codename

    def exec_work(self, work):
        if work.objtype == WorkObject.INV:
            if work.action == WorkObject.CREATE:
                data = self.invmeta_to_sale(work.content)
                action = 'POST'
            elif work.action == WorkObject.DELETE:
                data = Sale(seller_inv_uid=work.objid, seller_codename=self.codename)
                action = 'DELETE'
            desturl = '/import/client_sale'
        else:
            with self.dbapi.session:
                data = self.make_inv_movement(work)
            action = 'POST'
            desturl = '/import/inv_movement_set'
        url = urljoin(self.root_url, desturl)
        r = requests.request(action, url,
                             auth=self.auth,
                             data=json_dumps(data))
        return r

    def forward_request(self, work):
        print('work', work['work'], type(work['work']))
        work = work['work']
        work = WorkObject.deserialize(json.loads(work))
        if work.objtype == WorkObject.INV:
            if work.action == WorkObject.DELETE:
                work.content = InvMovementMeta(uid=work.objid)
            else:
                work.content = InvMetadata.deserialize(work.content)
        elif work.objtype == WorkObject.INV_TRANS:
            work.content = Invoice.deserialize(work.content)
        elif work.objtype == WorkObject.TRANS:
            work.content = Transferencia.deserialize(work.content)
        else:
            print('ERROR')
            return -1 # RETRY
        r = self.exec_work(work)
        if r.status_code == 200:
            return -2  # OK
        else:
            return -1  # RETRY

    def make_inv_movement(self, work):
        invmeta = InvMovementMeta()
        doc = work.content
        if work.objtype == WorkObject.INV_TRANS:
            invmeta.timestamp = doc.meta.timestamp
            invmeta.value_usd = old_div(Decimal(doc.meta.subtotal - (doc.meta.discount or 0)), 100)
            invmeta.inventory_docid = doc.meta.uid
            invmeta.trans_type = InvMovementType.SALE
            invmeta.origin = doc.meta.bodega_id
            invmeta.dest = -1
        else:
            invmeta.timestamp = doc.meta.timestamp
            invmeta.value_usd = doc.meta.value
            invmeta.inventory_docid = doc.meta.uid
            invmeta.origin = doc.meta.origin
            invmeta.dest = doc.meta.dest
            invmeta.trans_type = transtype_to_invtype(doc.meta.trans_type)
        invmeta.inventory_codename = self.codename
        items = []
        if work.action == WorkObject.DELETE:
            invmeta.origin, invmeta.dest = invmeta.dest, invmeta.origin
            invmeta.trans_type = InvMovementType.delete_type(invmeta.trans_type)
            invmeta.timestamp = datetime.datetime.now()  # record delete time which is different than invoice time
        for trans in doc.items_to_transaction(self.dbapi):
            itemgroup = self.dbapi.get(trans.itemgroup_id, ProdItemGroup)
            items.append(ItemGroupCant(cant=trans.quantity, itemgroup=itemgroup))
        return InvMovementFull(meta=invmeta, items=items)

    def invmeta_to_sale(self, meta):
        sale = Sale()
        sale.timestamp = meta.timestamp
        sale.client_id = meta.client.codigo
        sale.seller_ruc = meta.almacen_ruc
        sale.seller_inv_uid = meta.uid
        sale.invoice_code = meta.codigo
        sale.pretax_amount_usd = old_div(Decimal(meta.subtotal - (meta.discount or 0)), 100)
        sale.tax_usd = old_div(Decimal(meta.tax or 0), 100)
        sale.status = Status.NEW
        sale.user_id = meta.user
        sale.payment_format = meta.payment_format
        sale.seller_codename = self.codename
        if getattr(meta, 'almacen_id', None):
            meta.payment_format = 'None'
        return sale
