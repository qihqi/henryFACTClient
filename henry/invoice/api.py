import json
import os
import uuid
from decimal import Decimal
from typing import Dict, Optional, List, cast

from jinja2 import Environment
from bottle import Bottle, request, abort
import datetime

from henry.base.auth import AuthType
from henry.base.dbapi import DBApiGeneric
from henry.base.fileservice import FileService
from henry import constants, common

from henry.base.serialization import json_dumps
from henry.base.session_manager import DBContext
from henry.invoice.dao import SRINota, SRINotaStatus

from .dao import Invoice
from .util import compute_access_code
from .util import generate_xml_paths

__author__ = 'han'

_ALM_ID_TO_INFO = {
    1: {
        'ruc': constants.RUC,
        'name': constants.NAME,
    },
    3: {
        'ruc': constants.RUC_CORP,
        'name': constants.NAME_CORP,
    },
    99: {
        'ruc': 'RUCRUCRUC',
        'name': 'NAMENAMENAME',
    }
}


class IdType:
    RUC = '04'
    CEDULA = '05'
    CONS_FINAL = '07'


def guess_id_type(client_id):
    if len(client_id) == 10:
        return IdType.CEDULA
    if len(client_id) > 10:
        return IdType.RUC
    return IdType.CONS_FINAL


def inv_to_sri_dict(inv: Invoice, sri_nota: SRINota) -> Optional[Dict]:
    """Return the dict used to render xml."""
    assert inv.meta
    assert inv.meta.client
    assert inv.meta.timestamp is not None
    if inv.meta.almacen_id is None:
        return None
    info = _ALM_ID_TO_INFO.get(inv.meta.almacen_id)
    if info is None:
        return None
    tipo_ident = guess_id_type(inv.meta.client.codigo)
    # 99 para consumidor final
    id_compra = '99' if tipo_ident == IdType.CONS_FINAL else inv.meta.client.codigo
    ts = inv.meta.timestamp
    access = sri_nota.access_code
    if access is None:
        access = compute_access_code(inv)
    res = {
        'ambiente': 1,
        'razon_social': info['name'],
        'ruc': info['ruc'],
        'clave_acceso': access,
        'codigo': '{:09}'.format(int(inv.meta.codigo or 0)),
        'dir_matriz': 'Boyaca 1515 y Aguirre',
        'fecha': '{:02}/{:02}/{:04}'.format(ts.day, ts.month, ts.year),
        'tipo_identificacion_comprador': tipo_ident,
        'id_comprador': id_compra,
        'razon_social_comprador': inv.meta.client.fullname,
        'subtotal': Decimal(inv.meta.subtotal or 0) / 100,
        'iva': Decimal(inv.meta.tax or 0) / 100,
        'descuento': Decimal(inv.meta.discount or 0) / 100,
        'total': Decimal(inv.meta.total or 0) / 100,
        'tax_percent': inv.meta.tax_percent,
        'detalles': []
    }
    for item in inv.items:
        assert item.prod is not None
        assert item.prod.precio1 is not None
        assert item.prod.precio2 is not None
        assert item.cant is not None
        assert item.prod.cant_mayorista is not None
        if item.cant > item.prod.cant_mayorista:
            desc = (item.prod.precio1 - item.prod.precio2) * item.cant
        else:
            desc = Decimal(0)
        total_sin_impuesto = item.prod.precio1 * item.cant - desc
        total_impuesto = Decimal('0.12') * total_sin_impuesto
        item_dict = {
            'id': item.prod.pid,
            'nombre': item.prod.nombre,
            'cantidad': item.cant,
            'precio': Decimal(item.prod.precio1) / 100,
            'descuento': Decimal(desc) / 100,
            'total_sin_impuesto': Decimal(total_sin_impuesto) / 100,
            'total_impuesto': Decimal(total_impuesto) / 100
        }
        cast(List, res['detalles']).append(item_dict)
    return res


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
        loaded = json.loads(msg_decoded)
        inv_json = loaded['inv']
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
    @dbcontext
    def gen_xml(uid):
        uid = int(uid)
        sri_nota = dbapi.get(uid, SRINota)
        relpath, signed_path = generate_xml_paths(
            sri_nota, file_manager, jinja_env, dbapi)

        return {'result': signed_path}

    @api.get('{}/mark_remote_nota_as_valid/<uid>')
    @dbcontext
    def mark_remote_nota_as_valid(uid):
        uid = int(uid)
        sri_nota = dbapi.get(uid, SRINota)
        result = CommResult(
            status='success',
            request_type='AUTORIZAR',
            request_sent='',
            response='Marcado manualmente como autorizado',
            environment=SRI_ENV_PROD,
            timestamp=datetime.datetime.now(),
        )
        sri_nota.append_comm_result(result, file_manager, dbapi)
        dbapi.update(sri_nota, {
            'status': SRINotaStatus.CREATED_SENT_VALIDATED
        })

        return {'status': 'success'}

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

    return api
