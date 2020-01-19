from __future__ import division
from __future__ import print_function
from past.utils import old_div
from decimal import Decimal

from bottle import Bottle, request, abort
import datetime

from henry import constants

from henry.background_sync.worker import WorkObject, doc_to_workobject

from henry.base.serialization import SerializableMixin, json_loads, json_dumps
from henry.base.session_manager import DBContext
from henry.dao.document import Status

from henry.product.dao import Store, PriceList, create_items_chain
from henry.users.dao import User, Client

from .coreschema import NNota
from .dao import Invoice

__author__ = 'han'

_ALM_ID_TO_INFO = {
    1: {
        'ruc': constants.RUC,
        'name': constants.NAME,
    },
    3: {
        'ruc': constants.RUC_CORP
        'name': constants.NAME_CORP,
    }
}


def inv_to_sri_dict(inv):
    """Return the dict used to render xml."""
    info = _ALM_ID_TO_INFO.get(inv.almacen_id)
    # TODO
    tipo_ident = '99' if inv.meta.client.codigo == 'NA' else None
    id_compra = '99' if inv.meta.client.codigo == 'NA' else inv.meta.client.codigo
    return {
      'ambiente': 1,
      'razon_social': info['name'],
      'ruc': info['ruc'],
      'clave_access': '',
      'codigo': inv.meta.codigo,
      'dir_matriz': 'Boyaca 1515 y Aguirre',
      'fecha': inv.meta.timestamp.date().isoformat(),
      'tipo_identificacion_comprador': tipo_ident,
      'id_comprador': id_compra,
      'subtotal': inv.meta.subtotal,
      'iva': inv.meta.tax,
      'descuento': inv.meta.discount,
      'total': inv.meta.total,
      'detalles': [
          {
              'nombre': item.nombre,
              'cantidad': item.cant,
              'precio': item.precio1,
              'descuento': item.precio2 - item.precio1,
              'total_sin_impuesto': item.precio1 * item.cant,
          } for item in inv.items]
    }


def make_nota_all(url_prefix, dbapi, actionlogged,
                  file_manager, auth_decorator):

    api = Bottle()
    dbcontext = DBContext(dbapi.session)
    # ########## NOTA ############################

    @api.post('{}/srinota'.format(url_prefix))
    @dbcontext
    @auth_decorator(2)
    @actionlogged
    def create_sri_nota():
        json_content = request.body.read().decode('utf-8')
        if not json_content:
            return ''

        inv_json = json_loads(json_content)
        inv = Invoice.deserialize(inv_json)

        prefix = os.path.join('srinota',
                datetime.date.toda().isoformat(),
                uuid.uuid4().hex)

        file_manager.put_file(prefix + '.json', inv_json)

        # gen xml
        inv_xml = ...
        file_manager.put_file(prefix + '.xml', inv_xml)

        row = SRINota()
        row.almacen_ruc = inv.almancenruc
        row.orig_codigo = inv.codigo
        row.timestamp_received = datetime.datetime.now()
        row.status = SRINotaStatus.CREATED
        row.json_inv_location = prefix + '.json'
        row.xml_inv_location = prefix + '.xml'
        row.resp1_location = ''
        row.resp2_location = ''
        pkey = dbapi.create(row)
        return {'created': pkey}


    @api.delete('{}/srinota')
    @dbcontext
    @auth_decorator(2)
    @actionlogged
    def postear_invoice(uid):
        pass


    return api
