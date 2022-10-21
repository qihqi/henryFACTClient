import json
import os
import uuid

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
            res = dbapi.search(SRINota,
                               **{'timestamp_received-gte': start_date,
                                  'timestamp_received-lte': end_date})
        return json_dumps(list(res))

    return api
