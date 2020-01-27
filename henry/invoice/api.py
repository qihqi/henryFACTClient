import os
import uuid

from jinja2 import Environment
from bottle import Bottle, request, abort
import datetime

from henry.base.auth import AuthType
from henry.base.dbapi import DBApiGeneric
from henry.base.fileservice import FileService
from henry import constants, common

from henry.base.serialization import json_loads, json_dumps
from henry.base.session_manager import DBContext
from henry.invoice.dao import SRINota, SRINotaStatus

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


def make_nota_all(url_prefix: str, dbapi: DBApiGeneric,
                  jinja_env: Environment,
                  file_manager: FileService, auth_decorator: AuthType):

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

        existing = dbapi.search(
            SRINota,
            almacen_ruc=inv.meta.almacen_ruc,
            orig_codigo=inv.meta.codigo)

        if existing:
            return {'created': '', 'msg': 'ya exist'}


        row = SRINota()
        row.almacen_ruc = inv.meta.almacen_ruc
        row.orig_codigo = inv.meta.codigo
        row.orig_timestamp = inv.meta.timestamp
        row.timestamp_received = datetime.datetime.now()
        row.status = SRINotaStatus.CREATED
        row.total = inv.meta.total
        if inv.meta.client:
            row.buyer_ruc = inv.meta.client.codigo
            row.buyer_name = inv.meta.client.fullname
        row.tax = inv.meta.tax
        row.json_inv_location = prefix + '.json'
        row.xml_inv_location = ''
        row.resp1_location = ''
        row.resp2_location = ''
        pkey = dbapi.create(row)
        return {'created': pkey}

    @api.post('{}/gen_xml/<uid>'.format(url_prefix))
    def gen_xml(uid):
        uid = int(uid)
        sri_nota = dbapi.get(uid, SRINota)
        inv_text = file_manager.get_file(sri_nota.json_inv_location)
        if inv_text is None:
            return {'result': 'no_inv'}

        inv_dict = json_loads(inv_text)
        inv = Invoice.deserialize(inv_dict)

        xml_dict = inv_to_sri_dict(inv)
        xml_text = jinja_env.get_template(...).render(xml_dict)

        file_manager.put_file(sri_nota.xml_inv_location, xml_text)
        return {'result': xml_text}

    @api.get('{}/remote_nota'.format(url_prefix))
    def get_extended_nota():
        start = request.query.get('start')
        end = request.query.get('end')
        if start is None or end is None:
            abort(400, 'invalid input')
        datestrp = datetime.datetime.strptime
        start_date = datestrp(start, "%Y-%m-%d")
        end_date = datestrp(end, "%Y-%m-%d")
        with dbapi.session:
            res = dbapi.search(SRINota, **{'timestamp_received-gte': start_date,
                            'timestamp_received-lte': end_date})
        return json_dumps(list(res))

    @api.get('{}/view_nota'.format(url_prefix))
    def view_nota():
        start = request.query.get('start')
        end = request.query.get('end')
        temp = jinja_env.get_template('invoice/sync_invoices_form.html')
        if start is None or end is None:
            return temp.render(rows=[])
        datestrp = datetime.datetime.strptime
        start_date = datestrp(start, "%Y-%m-%d")
        end_date = datestrp(end, "%Y-%m-%d")
        with dbapi.session:
            res = dbapi.search(SRINota, **{'timestamp_received-gte': start_date,
                                           'timestamp_received-lte': end_date})
        print(res)
        return temp.render(rows=res)


    return api
