from builtins import str
from builtins import map
from decimal import Decimal
from bottle import Bottle, request, abort

from henry.base.serialization import json_dumps
from henry.base.session_manager import DBContext
from henry.bottlehelper import get_property_or_fail

from .dao import Store, PriceList

__author__ = 'han'


def mult_thousand(prod):
    if prod.cant_mayorista:
        prod.cant_mayorista *= 1000


def convert_to_cent(dec):
    if not isinstance(dec, Decimal):
        dec = Decimal(dec)
    return int(dec * 100)




def make_search_pricelist_api(api_url_prefix, actionlogged, dbapi):
    api = Bottle()
    dbcontext = DBContext(dbapi.session)

    @api.get('{}/alm/<almacen_id>/producto'.format(api_url_prefix))
    @dbcontext
    @actionlogged
    def searchprice(almacen_id):
        alm = dbapi.get(almacen_id, Store)
        prefijo = get_property_or_fail(request.query, 'prefijo')
        result = list(dbapi.search(PriceList, **{
            'nombre-prefix': prefijo,
            'almacen_id': alm.bodega_id}))

        # FIXME remove this hack when client side is ready
        use_thousandth = request.query.get('use_thousandth', 1)
        if int(use_thousandth):
            list(map(mult_thousand, result))
        return json_dumps(result)

    @api.get('{}/alm/<almacen_id>/producto/<prod_id:path>'.format(api_url_prefix))
    @dbcontext
    @actionlogged
    def get_price_by_id(almacen_id, prod_id):
        if int(almacen_id) == 3:
            almacen_id = 1
        prod = dbapi.getone(PriceList, prod_id=prod_id, almacen_id=almacen_id)
        if prod is None:
            abort(404)
        use_thousandth = request.query.get('use_thousandth', '1')
        if int(use_thousandth):
            mult_thousand(prod)
        return json_dumps(prod.serialize())

    @api.get(api_url_prefix + '/barcode/<bcode>')
    @dbcontext
    def get_barcoded_item(bcode):
        bcode = str(int(bcode))
        pos = 0
        for i, x in enumerate(bcode):
            if x == '0':
                pos = i
                break
        cant = int(bcode[:pos])
        pid = int(bcode[pos:-1])
        price = dbapi.get(pid, PriceList)
        if price is None:
            price = dbapi.get(bcode[pos:], PriceList)
            if price is None:
                abort(404)
        result = {}
        mult_thousand(price)
        result['prod'] = price
        result['cant'] = cant
        return json_dumps(result)

    return api  ## END BLOCK


