import json
from decimal import Decimal

import barcode
import os
from bottle import Bottle, request, redirect
from henry.base.common import parse_start_end_date
from henry.base.dbapi_rest import bind_dbapi_rest
from henry.base.serialization import json_dumps
from henry.product.dao import ProdItemGroup, Store, Bodega, ProdItem, PriceList


def validate_full_item(content, dbapi):
    prod_id = content['prod']['prod_id']
    if dbapi.getone(ProdItemGroup, prod_id=prod_id) is not None:
        return False, 'Codigo ya existe'
    if len([x for x in content['items'] if int(x['multiplier']) == 1]) != 1:
        return False, 'Debe haber un unidad con multiplicador 1'
    all_mult = set()
    for i in content['items']:
        if i['multiplier'] in all_mult:
            return False, 'Todos las unidades debe tener multiplicador distintos'
        all_mult.add(i['multiplier'])
    return True, ''


def make_full_items(itemgroup, items, prices_by_prod_id):
    """
    {
        "prod" : {prod_id, name, desc, base_unit}< - information on item group
        "items": [multiplier, unit
                  "prices": {
                    "display_name":
                    "price1":
                    "price2":
                    "cant":
    }, ...
    ]<- information on items requires multiplier be distinct
    }
    """

    result = {'prod': itemgroup.serialize(), 'items': []}
    for x in items:
        new_item = x.serialize()
        new_item['prices'] = []
        for pl in prices_by_prod_id[x.prod_id]:
            new_item['prices'].append(pl)
        result['items'].append(new_item)
    return result

def make_wsgi_api(prefix, sessionmanager, dbcontext, auth_decorator, dbapi, inventoryapi):
    app = Bottle()

    @app.post(prefix + '/item_full')
    @dbcontext
    @auth_decorator
    def create_item_full():
        """
            input format:
            {
                "prod" : {prod_id, name, desc, base_unit}< - information on item group
                "items": [{multiplier}, {unit}<- information on items requires multiplier be distinct
                "prices": [{unit, almacen_id, display_name, price1, price2, cant}]
                "new_unit": []
            }
        """

        content = request.body.read()
        content = json.loads(content)
        valid, message = validate_full_item(content, dbapi)
        if not valid:
            return {'status': 'failure', 'msg': message}
        create_full_item_from_dict(dbapi, content)
        sessionmanager.session.commit()
        return {'status': 'success'}

    @app.get(prefix + '/item_full/<item_id>')
    @dbcontext
    def get_item_full(item_id):
        itemgroup = dbapi.get(item_id, ProdItemGroup)
        items = dbapi.search(ProdItem, itemgroupid=itemgroup.uid)
        prices_by_item = {}
        for x in items:
            prices_by_item[x.prod_id] = dbapi.search(PriceList, prod_id=x.prod_id)
        return json_dumps(make_full_items(itemgroup, items, prices_by_item))

    @app.post(prefix + '/item_with_price')
    @dbcontext
    def save_item_with_price():
        # TODO: VALIDATION
        item_with_price = json.loads(request.body.read())
        item = ProdItem.deserialize(item_with_price)
        prod_id = item_with_price['prod_id']
        if int(item_with_price['multiplier']) > 1:
            prod_id += '+'
        item.prod_id = prod_id
        uid = dbapi.create(item)
        for aid, x in item_with_price['price'].items():
            p = PriceList()
            p.almacen_id = aid
            p.prod_id = prod_id
            p.precio1 = int(Decimal(x['price1']) * 100)
            p.precio2 = int(Decimal(x['price2']) * 100)
            p.nombre = x['display_name']
            p.cant_mayorista = x['cant']
            p.unidad = item.unit
            p.multiplicador = item.multiplier
            dbapi.create(p)
        dbapi.db_session.commit()
        return {'status': 'success', 'uid': uid}

    @app.get(prefix + '/prod_quantity/<uid>')
    @dbcontext
    def get_prod_quantity(uid):
        current_record = inventoryapi.get_current_quantity(uid)
        bodegas = dbapi.search(Bodega)
        return json_dumps({
            'inv': bodegas,
            'itemgroup_id': uid,
            'quantity': current_record
        })

    @app.get(prefix + '/itemgroup/<uid>/transaction')
    @dbcontext
    def get_transactions_of_item_group(uid):
        start, end = parse_start_end_date(request.query)
        return json_dumps({'results': list(inventoryapi.list_transactions(uid, start, end))})

    bind_dbapi_rest(prefix + '/pricelist', dbapi, PriceList, app)
    bind_dbapi_rest(prefix + '/itemgroup', dbapi, ProdItemGroup, app)
    bind_dbapi_rest(prefix + '/item', dbapi, ProdItem, app)
    return app


def make_wsgi_app(dbcontext, auth_decorator, jinja_env, dbapi, imagefiles):
    w = Bottle()

    @w.get('/app/ver_lista_precio')
    @dbcontext
    @auth_decorator
    def ver_lista_precio():
        almacen_id = int(request.query.get('almacen_id', 1))
        prefix = request.query.get('prefix', None)
        if prefix:
            prods = dbapi.search(PriceList, **{'nombre-prefix': prefix,
                                               'almacen_id': almacen_id})
        else:
            prods = []
        temp = jinja_env.get_template('prod/ver_lista_precio.html')
        return temp.render(
            prods=prods, stores=dbapi.search(Store), prefix=prefix,
            almacen_name=dbapi.get(almacen_id, Store).nombre)

    @w.get('/app/barcode_form')
    @dbcontext
    @auth_decorator
    def barcode_form():
        msg = request.query.msg
        temp = jinja_env.get_template('prod/barcode_form.html')
        return temp.render(alms=dbapi.search(Store), msg=msg)

    @w.get('/app/barcode')
    @dbcontext
    @auth_decorator
    def get_barcode():
        prod_id = request.query.get('prod_id')
        almacen_id = request.query.get('almacen_id')
        quantity = int(request.query.get('quantity', 1))

        prod = dbapi.getone(PriceList, prod_id=prod_id, almacen_id=almacen_id)

        if quantity > 1000:
            redirect('/app/barcode_form?msg=cantidad+muy+grande')

        if not prod:
            redirect('/app/barcode_form?msg=producto+no+existe')

        encoded_string = '{:03d}{:09d}'.format(quantity, prod.pid)
        bar = barcode.EAN13(encoded_string)
        filename = bar.ean + '.svg'
        path = imagefiles.make_fullpath(filename)
        if not os.path.exists(path):
            with open(path, 'w') as barcode_file:
                bar.write(barcode_file)
        url = '/app/img/{}'.format(filename)

        column = 5
        row = 9
        price = int(prod.precio1 * quantity * Decimal('1.14') + Decimal('0.5'))

        temp = jinja_env.get_template('prod/barcode.html')
        return temp.render(url=url, row=row, column=column, prodname=prod.nombre, price=price)
    return w


def create_full_item_from_dict(dbapi, content):
    """
        input format:
        {
            "prod" : {prod_id, name, desc, base_unit}< - information on item group
            "items": [multiplier, unit
                "prices": {
                   "display_name":
                   "price1":
                   "price2":
                   "cant":
                }, ...
                ]<- information on items requires multiplier be distinct
        }
        must be called within dbcontext
    """
    itemgroup = ProdItemGroup()
    itemgroup.merge_from(content['prod'])

    itemgroupid = dbapi.create(itemgroup)

    items = {}
    allstores = {x.almacen_id: x for x in dbapi.search(Store)}

    for item in content['items']:
        prices = item['prices']
        del item['prices']
        i = ProdItem()
        i.merge_from(item)
        i.itemgroupid = itemgroupid
        if i.multiplier == 1:
            i.prod_id = itemgroup.prod_id
        elif i.multiplier > 1:
            i.prod_id = itemgroup.prod_id + '+'
        elif i.multiplier < 1:
            i.prod_id = itemgroup.prod_id + '-'

        item_id = dbapi.create(i)
        items[i.unit] = i

        # create prices
        for alm_id, p in prices.items():
            price = PriceList()
            price.nombre = p['display_name']
            price.precio1 = int(float(p['price1']) * 100)
            price.precio2 = int(float(p['price2']) * 100)
            price.cant_mayorista = p['cant']
            price.prod_id = i.prod_id
            price.unidad = i.unit
            price.almacen_id = int(alm_id)
            price.multiplicador = i.multiplier
            dbapi.create(price)
