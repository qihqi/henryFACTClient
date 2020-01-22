from __future__ import division
from __future__ import print_function
from past.utils import old_div
import os
import uuid
from decimal import Decimal

from bottle import Bottle, request, abort
import datetime

from henry import constants, common

from henry.background_sync.worker import WorkObject, doc_to_workobject

from henry.base.serialization import SerializableMixin, json_loads, json_dumps
from henry.base.session_manager import DBContext
from henry.dao.document import Status
from henry.invoice.dao import SRINota, SRINotaStatus

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
        'ruc': constants.RUC_CORP,
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

    @api.post('{}/remote_nota'.format(url_prefix))
    @dbcontext
    def create_sri_nota():
        msg = request.body.read()
        if not msg:
            return ''
        msg_decoded = common.aes_decrypt(msg).decode('utf-8')
        loaded = json_loads(msg_decoded)
        inv_json = loaded['inv']
        method = loaded['method']
        inv = Invoice.deserialize(inv_json)

        prefix = os.path.join('remote_nota',
            datetime.date.today().isoformat(),
            uuid.uuid4().hex)

        file_manager.put_file(prefix + '.json', json_dumps(inv_json))

        # gen xml
        # inv_xml = ...
        # file_manager.put_file(prefix + '.xml', inv_xml)

        row = SRINota()
        row.almacen_ruc = inv.meta.almacen_ruc
        row.orig_codigo = inv.meta.codigo
        row.timestamp_received = datetime.datetime.now()
        row.status = SRINotaStatus.CREATED
        row.json_inv_location = prefix + '.json'
        row.xml_inv_location = prefix + '.xml'
        row.resp1_location = ''
        row.resp2_location = ''
        pkey = dbapi.create(row)
        return {'created': pkey}

    return api
