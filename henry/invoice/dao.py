import datetime
import os
import uuid
from henry.base.serialization import SerializableMixin, DbMixin, parse_iso_datetime
from henry.dao.document import MetaItemSet
from henry.product.dao import InventoryMovement, ProdItem, InvMovementType, get_real_prod_id
from henry.users.dao import Client

from .coreschema import NNota

__author__ = 'han'


class PaymentFormat:
    CASH = "efectivo"
    CARD = "tarjeta"
    CHECK = "cheque"
    DEPOSIT = "deposito"
    CREDIT = "credito"
    VARIOUS = "varios"
    names = (
        CASH,
        CARD,
        CHECK,
        DEPOSIT,
        CREDIT,
        VARIOUS,
    )


class InvMetadata(SerializableMixin, DbMixin):
    _db_class = NNota
    _excluded_vars = ('users',)
    _db_attr = {
        'uid': 'id',
        'codigo': 'codigo',
        'user': 'user_id',
        'timestamp': 'timestamp',
        'status': 'status',
        'total': 'total',
        'tax': 'tax',
        'tax_percent': 'tax_percent',
        'discount_percent': 'discount_percent',
        'subtotal': 'subtotal',
        'discount': 'discount',
        'bodega_id': 'bodega_id',
        'paid': 'paid',
        'paid_amount': 'paid_amount',
        'almacen_id': 'almacen_id',
        'almacen_name': 'almacen_name',
        'almacen_ruc': 'almacen_ruc',
        'payment_format': 'payment_format',
        'retension': 'retension',
    }

    _name = tuple(_db_attr.keys()) + ('users', 'client')

    def __init__(
            self,
            uid=None,
            codigo=None,
            client=None,
            user=None,
            timestamp=None,
            status=None,
            total=None,
            tax=None,
            subtotal=None,
            discount=None,
            bodega_id=None,
            tax_percent=None,
            discount_percent=None,
            paid=None,
            paid_amount=None,
            payment_format=None,
            almacen_id=None,
            almacen_name=None,
            almacen_ruc=None,
            retension=None):
        self.uid = uid
        self.codigo = codigo
        self.client = client
        self.user = user
        self.timestamp = timestamp
        self.status = status
        self.total = total
        self.tax = tax
        self.subtotal = subtotal
        self.discount = discount
        self.bodega_id = bodega_id
        self.almacen_id = almacen_id
        self.almacen_name = almacen_name
        self.almacen_ruc = almacen_ruc
        self.tax_percent = tax_percent
        self.discount_percent = discount_percent
        self.paid = paid
        self.payment_format = payment_format
        self.paid_amount = paid_amount
        self.retension = retension

    @classmethod
    def deserialize(cls, the_dict):
        x = cls().merge_from(the_dict)
        if x.timestamp and not isinstance(x.timestamp, datetime.datetime):
            x.timestamp = parse_iso_datetime(x.timestamp)
        if 'client' in the_dict:
            client = Client.deserialize(the_dict['client'])
            x.client = client
        else:
            x.client = None
        return x

    def db_instance(self):
        db_instance = super(InvMetadata, self).db_instance()
        db_instance.client_id = self.client.codigo
        return db_instance

    @classmethod
    def from_db_instance(cls, db_instance):
        this = super(InvMetadata, cls).from_db_instance(db_instance)
        this.client = Client()
        this.client.codigo = db_instance.client_id
        return this


class Invoice(MetaItemSet):
    _metadata_cls = InvMetadata

    def items_to_transaction(self, dbapi):
        for item in self.items:
            proditem = dbapi.getone(ProdItem, prod_id=item.prod.prod_id)
            yield InventoryMovement(
                from_inv_id=self.meta.bodega_id,
                to_inv_id=-1,
                quantity=(item.cant * item.prod.multiplicador),
                prod_id=get_real_prod_id(item.prod.prod_id),
                itemgroup_id=proditem.itemgroupid,
                type=InvMovementType.SALE,
                reference_id=str(self.meta.uid),
            )

    def validate(self):
        if getattr(self.meta, 'codigo', None) is None:
            raise ValueError('codigo cannot be None to save an invoice')

    @property
    def filepath_format(self):
        path = getattr(self, '_path', None)
        if path is None:
            self._path = os.path.join(
                self.meta.timestamp.date().isoformat(), uuid.uuid1().hex)
        return self._path
