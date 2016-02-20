import json
from urlparse import urljoin
from decimal import Decimal
import requests

from henry.base.serialization import json_dumps, SerializableMixin
from henry.dao.document import Status
from henry.importation.dao import Sale
from henry.invoice.dao import InvMetadata


# What actions needs to be forwarded?

# create/post/delete nota
# create/post/delete ingreso
# create client
# create product
# alter product price (changes to pricelist)


class WorkObject(SerializableMixin):
    CREATE = 'create'
    POST = 'post'
    DELETE = 'delete'
    INV = 'inv'
    TRANS = 'trans'

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


def invmeta_to_sale(meta):
    sale = Sale()
    sale.timestamp = meta.timestamp
    sale.client_id = meta.client.codigo
    sale.seller_ruc = meta.almacen_ruc
    sale.seller_inv_uid = meta.uid
    sale.invoice_code = meta.codigo
    sale.pretax_amount_usd = Decimal(meta.subtotal - (meta.discount or 0)) / 100
    sale.tax_usd = Decimal(meta.tax) / 100
    sale.status = Status.NEW
    sale.user_id = meta.user
    sale.payment_format = meta.payment_format
    if getattr(meta, 'almacen_id', None):
        meta.payment_format = 'None'
    return sale


class ForwardRequestProcessor:

    def __init__(self, dbapi, root_url, auth, codename):
        self.dbapi = dbapi
        self.root_url = root_url
        self.auth = auth
        self.cookies = None
        self.codename = codename

    def forward_request(self, work):
        print 'work', work['work'], type(work['work'])
        work = work['work']
        des = WorkObject.deserialize(json.loads(work))
        des.content = InvMetadata.deserialize(des.content)
        work = des
        url = urljoin(self.root_url, '/import/client_sale')
        if work.action == WorkObject.CREATE:
            data = invmeta_to_sale(work.content)
            action = 'POST'
        else:
            data = Sale(seller_inv_uid=work.content.uid)
            action = 'DELETE'
        data.seller_codename = self.codename
        r = requests.request(action, url,
                             auth=self.auth,
                             data=json_dumps(data))
        if r.status_code == 200:
            return -2  # OK
        else:
            return -1  # RETRY
