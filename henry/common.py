from __future__ import division
from builtins import zip
from past.utils import old_div

import base64
import datetime
import hashlib
from decimal import Decimal

from bottle import abort
from Crypto.Cipher import AES

from henry import constants
from henry.base.common import parse_iso
from henry.base.serialization import json_dumps, json_loads
from henry.inventory.dao import TransMetadata, TransType, TransItem
from henry.product.dao import PriceList, ProdItemGroup


def get_base_price(dbapi, prod_id):
    plus = prod_id + '+'
    price = dbapi.search(PriceList, prod_id=plus, almacen_id=2)
    if not price:
        price = dbapi.search(PriceList, prod_id=prod_id, almacen_id=2)
    if not price:
        return None
    price = price[0]
    mult = price.multiplicador or 1
    return old_div(old_div(Decimal(price.precio1), 100), mult)


def items_from_form(dbapi, form):
    items = []
    for cant, prod_id in zip(
            form.getlist('cant'),
            form.getlist('codigo')):
        if not cant.strip() or not prod_id.strip():
            # skip empty lines
            continue
        try:
            cant = Decimal(cant)
        except ValueError:
            abort(400, 'cantidad debe ser entero positivo')
        if cant < 0:
            abort(400, 'cantidad debe ser entero positivo')
        itemg = dbapi.getone(ProdItemGroup, prod_id=prod_id)
        items.append(TransItem(itemg, cant))
    return items


def transmetadata_from_form(form):
    meta = TransMetadata()
    meta.dest = form.get('dest').decode('utf-8')
    meta.origin = form.get('origin').decode('utf-8')
    fecha = form.get('fecha').decode('utf-8')
    if fecha:
        fecha = parse_iso(fecha)
        meta.timestamp = datetime.datetime.combine(
            fecha.date(), datetime.datetime.now().time())
    try:
        meta.dest = int(meta.dest)
        meta.origin = int(meta.origin)
    except ValueError:
        pass
    meta.meta_type = form.get('meta_type')
    meta.trans_type = form.get('trans_type')
    if meta.trans_type == TransType.INGRESS:
        meta.origin = None  # ingress does not have origin
    if meta.trans_type in (TransType.EXTERNAL or TransType.EGRESS):
        meta.dest = None  # dest for external resides in other server
    if meta.timestamp is None:
        meta.timestamp = datetime.datetime.now()
    return meta

_MODE = AES.MODE_EAX
def aes_encrypt(text_bytes):
    """Returns a blob that contains(cipher_text, nonce, tag)."""
    m = hashlib.sha1()
    m.update(constants.AES_KEY.encode('utf-8'))
    key = m.digest()[:16]
    cipher = AES.new(key, _MODE)
    cipher_text, tag = cipher.encrypt_and_digest(text_bytes)
    content = [
        base64.b64encode(cipher_text).decode('ascii'), 
        base64.b64encode(cipher.nonce).decode('ascii'), 
        base64.b64encode(tag).decode('ascii')]
    return json_dumps(content).encode('utf-8')


def aes_decrypt(blob):
    """returns decrypted text or exception."""
    m = hashlib.sha1()
    m.update(constants.AES_KEY.encode('utf-8'))
    key = m.digest()[:16]
    blob_str = blob.decode('utf-8')
    json_decoded = json_loads(blob_str)
    cipher_text, nonce, tag = tuple(map(base64.b64decode, json_decoded))
    cipher = AES.new(key, _MODE, nonce=nonce)
    plaintext = cipher.decrypt(cipher_text)
    cipher.verify(tag)
    return plaintext

