import json
from bottle import Bottle, request
from decimal import Decimal

from .dao import (Product, ProdItem, ProdItemGroup, PriceList,
    PriceListLabel, Inventory, ProdCount)


def convert_to_cent(dec):
    if not isinstance(dec, Decimal):
        dec = Decimal(dec)
    return int(dec * 100)


def create_full_item_from_dict(
        itemgroupapi, itemapi, priceapi,
        storeapi, bodegaapi, inventoryapi,
        prodapi, contenidoapi,
        content):
    '''
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
    '''
    itemgroup = ProdItemGroup()
    itemgroup.merge_from(content['prod'])

    itemgroupid = itemgroupapi.create(itemgroup)

    prod = Product()
    prod.nombre = itemgroup.name
    prod.codigo = itemgroup.prod_id
    prodapi.create(prod)

    items = {}
    inventories = {}
    allstores = {x.almacen_id: x for x in storeapi.search()}

    conts = {}
    for bod in bodegaapi.search():
        if bod.id == -1:
            continue
        contenido = ProdCount()
        contenido.bodega_id = bod.id
        contenido.prod_id = itemgroup.prod_id
        contenido.cant = 0
        contenido.precio = 0
        contenido.precio2 = 0
        cid = contenidoapi.create(contenido)
        conts[bod.id] = cid

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

        item_id = itemapi.create(i)
        items[i.unit] = i

        # create bodega
        invs = {}
        for bod in bodegaapi.search():
            if bod.id == -1:
                continue
            inv = Inventory()
            inv.item_id = item_id
            inv.bodega_id = bod.id
            inv.cant = 0
            inv_id = inventoryapi.create(inv)
            invs[bod.id] = inv

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
            bodid = allstores[price.almacen_id].bodega_id
            price.upi = conts[bodid]
            price.multiplicador = i.multiplier
            priceapi.create(price)


def validate_full_item(content, prodapi):
    prod_id = content['prod']['prod_id']
    if prodapi.get(prod_id) is not None:
        return False, 'Codigo ya existe'
    if len([x for x in content['items'] if int(x['multiplier']) == 1]) != 1:
        return False, 'Debe haber un unidad con multiplicador 1'
    all_mult = set()
    for i in content['items']:
        if i['multiplier'] in all_mult:
            return False, 'Todos las unidades debe tener multiplicador distintos'
        all_mult.add(i['multiplier'])
    return True, ''


def make_wsgi_api(sessionmanager, dbcontext, auth_decorator,
                  storeapi, prodapi, priceapi, itemapi, itemgroupapi,
                  bodegaapi, inventoryapi, contenidoapi):

    app = Bottle()

    @app.post('/prodapi/item_full')
    @dbcontext
    @auth_decorator
    def create_item_full():
        '''
            input format:
            {
                "prod" : {prod_id, name, desc, base_unit}< - information on item group
                "items": [{multiplier}, {unit}<- information on items requires multiplier be distinct
                "prices": [{unit, almacen_id, display_name, price1, price2, cant}]
                "new_unit": []
            }
        '''

        content = request.body.read()
        content = json.loads(content)
        valid, message = validate_full_item(content, prodapi)
        if not valid:
            return {'status': 'failure', 'msg': message}
        create_full_item_from_dict(
            itemgroupapi=itemgroupapi,
            itemapi=itemapi,
            priceapi=priceapi,
            storeapi=storeapi,
            bodegaapi=bodegaapi,
            inventoryapi=inventoryapi,
            prodapi=prodapi,
            contenidoapi=contenidoapi,
            content=content,
        )
        sessionmanager.session.commit()
        return {'status': 'success'}

    return app
