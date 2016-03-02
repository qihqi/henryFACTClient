from decimal import Decimal

from bottle import Bottle, request, abort
import datetime

from henry.base.serialization import SerializableMixin, json_loads, json_dumps
from henry.base.session_manager import DBContext

from henry.product.dao import Store, PriceList
from henry.users.dao import User, Client

from .coreschema import NNota
from .dao import Invoice

__author__ = 'han'


class InvoiceOptions(SerializableMixin):
    _name = ('crear_cliente', 'revisar_producto',
             'incrementar_codigo', 'usar_decimal', 'no_alm_id')

    def __init__(self):
        self.crear_cliente = False
        self.revisar_producto = False
        self.incrementar_codigo = False
        self.usar_decimal = False
        self.no_alm_id = False


def fix_inv_by_options(dbapi, inv, options):
    inv.items = filter(lambda x: x.cant >= 0, inv.items)
    inv.meta.paid = True
    for item in inv.items:
        if options.usar_decimal:
            item.cant = Decimal(item.cant)
        else:
            # if not using decimal, means that cant is send as int.
            # treating it as a decimal of 3 decimal places.
            item.cant = Decimal(item.cant) / 1000

        # this is an effort so that the prod coming from
        # invoice is incomplete. So it attempts so complete it with updated data
        if getattr(item.prod, 'upi', None) is None:
            alm_id = inv.meta.almacen_id
            if alm_id != 2:
                alm_id = 1
            print item.prod.prod_id, alm_id
            newprod = dbapi.search(PriceList, prod_id=item.prod.prod_id,
                                   almacen_id=alm_id)[0]
            item.prod.upi = newprod.upi
            item.prod.multiplicador = newprod.multiplicador

    # Get store: if ruc exists get it takes prescendence. Then name, then id.
    # The reason is that id is mysql autoincrement integer and may not be
    # consistent across different servers
    ruc = getattr(inv.meta, 'almacen_ruc', None)
    name = getattr(inv.meta, 'almacen_name', None)

    all_stores = dbapi.search(Store)

    def get_store_by(attr, value):
        temp = [x for x in all_stores if getattr(x, attr) == value]
        if temp:
            return temp[0]
        return None

    alm = None

    # using None as default value is buggy. Because there could
    # be store with store.ruc == None. That's why the if statement is needed
    if ruc:
        alm = get_store_by('ruc', ruc)
    if name and alm is None:
        alm = get_store_by('nombre', name)
    if alm is None:
        alm = get_store_by('almacen_id', inv.meta.almacen_id)

    # FIXME huge hack!!
    if alm is None:
        print 'save nota huge hack corpesut'
        if ruc.upper() == 'CORPESUT':
            alm = dbapi.get(3, Store)

    inv.meta.almacen_id = alm.almacen_id
    if options.no_alm_id:
        inv.meta.almacen_id = None
    inv.meta.almacen_name = alm.nombre
    inv.meta.almacen_ruc = alm.ruc
    inv.meta.bodega_id = alm.bodega_id


def parse_invoice_and_options(content_dict):
    options = InvoiceOptions()
    if 'options' in content_dict:
        op = content_dict['options']
        options.merge_from(op)
        del content_dict['options']

    inv = Invoice.deserialize(content_dict)
    return inv, options


def create_prod_if_not_exist(inv):
    pass


def make_nota_api(url_prefix, dbapi, actionlogged, invapi, auth_decorator, pedidoapi):
    api = Bottle()
    dbcontext = DBContext(dbapi.session)
    # ########## NOTA ############################

    @api.post('{}/nota'.format(url_prefix))
    @dbcontext
    @auth_decorator
    @actionlogged
    def create_invoice():
        json_content = request.body.read()
        if not json_content:
            return ''

        content = json_loads(json_content)
        inv, options = parse_invoice_and_options(content)
        fix_inv_by_options(dbapi, inv, options)
        if inv.meta.timestamp is None:
            inv.meta.timestamp = datetime.datetime.now()
        # at this point, inv should no longer change

        if options.crear_cliente:  # create client if not exist
            client = inv.meta.client
            if not dbapi.get(Client, client.codigo):
                dbapi.save(client)

        if options.revisar_producto:  # create producto if not exist
            create_prod_if_not_exist(inv)

        inv = invapi.save(inv)

        # increment the next invoice's number
        if options.incrementar_codigo:
            user = User(username=inv.meta.user)
            dbapi.update(user, {'last_factura': int(inv.meta.codigo) + 1})
        dbapi.db_session.commit()

        return {'codigo': inv.meta.uid}

    @api.put('{}/nota/<uid>'.format(url_prefix))
    @dbcontext
    @auth_decorator
    @actionlogged
    def postear_invoice(uid):
        inv = invapi.get_doc(uid)
        invapi.commit(inv)
        return {'status': inv.meta.status}

    @api.get(url_prefix + '/nota/<inv_id>')
    @dbcontext
    @auth_decorator
    @actionlogged
    def get_invoice(inv_id):
        doc = invapi.get_doc(inv_id)
        if doc is None:
            abort(404, 'Nota no encontrado')
            return
        return json_dumps(doc.serialize())

    @api.delete(url_prefix + '/nota/<uid>')
    @dbcontext
    @auth_decorator
    @actionlogged
    def delete_invoice(uid):
        inv = invapi.get_doc(uid)
        invapi.delete(inv)
        return {'status': inv.meta.status}

    # ####################### PEDIDO ############################
    @api.post(url_prefix + '/pedido')
    @dbcontext
    @auth_decorator
    @actionlogged
    def save_pedido():
        json_content = request.body.read()
        uid, _ = pedidoapi.save(json_content)
        return {'codigo': uid}

    @api.get(url_prefix + '/pedido/<uid>')
    @actionlogged
    def get_pedido(uid):
        f = pedidoapi.get_doc(uid)
        if f is None:
            abort(404, 'pedido no encontrado')
        return f

    return api


def get_inv_db_instance(session, almacen_id, codigo):
    return session.query(
        NNota.id, NNota.status, NNota.items_location).filter_by(
        almacen_id=almacen_id, codigo=codigo).first()