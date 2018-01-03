import sys
from henry.product.dao import *
from henry.base.dbapi import DBApiGeneric
from henry.coreconfig import sessionmanager
from decimal import Decimal
plist = {'upi': None, 'precio1': 48, 'precio2': 48, 'pid': None, 'multiplicador': Decimal('1.000'), 'almacen_id': 1, 'threshold': 0, 'nombre': u'ENCAJE 309', 'codigo': u'ENC309', 'unidad': None}

actions = []
with open(sys.argv[1]) as f:
    for line in f.readlines():
        actions.append(eval(line))

dbapi = DBApiGeneric(sessionmanager)
plist = PriceList.deserialize(plist)
def make_dict(pricelist):
    return {
        'prod': {
            'prod_id': pricelist.prod_id,
            'name': pricelist.nombre,
            'desc': pricelist.nombre,
            'base_unit': 'unidad',
        },
        'items': [{
            'multiplier': 1,
            'unit': 'unidad',
            'prices':{
                1: {
                'display_name': pricelist.nombre,
                'price1': pricelist.precio1 / 100.0,
                'price2': (pricelist.precio2 or pricelist.precio1) / 100.0,
                'cant': pricelist.cant_mayorista,
                }
            }
        }]
    }

d = make_dict(plist)

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


with dbapi.session:
    for action, item in actions:
        plist = PriceList.deserialize(item)
        if action == 'new':
            d = make_dict(plist)
            try:
                create_full_item_from_dict(dbapi, d)
            except Exception as e:
                print e
                dbapi.db_session.rollback()
                print 'ya existe', item
            else:
                print 'created', plist
        else:
            current = dbapi.getone(PriceList, almacen_id=plist.almacen_id,
                                   prod_id=plist.prod_id)
            if current is None:
                print 'no existe', item
                continue
            update_content = {
                'precio1': plist.precio1}
            if plist.precio2:
                update_content['precio2'] = plist.precio2
            dbapi.update(current, update_content)
            print 'updated', plist
        dbapi.db_session.commit()

