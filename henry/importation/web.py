from collections import defaultdict
import json
import datetime
from decimal import Decimal

from bottle import Bottle, request

from henry.base.dbapi_rest import bind_dbapi_rest
from henry.base.serialization import json_dumps
from henry.base.session_manager import DBContext
from .dao import (Purchase, PurchaseItem, UniversalProd, DeclaredGood,
                  get_purchase_full, get_custom_items_full, 
                  CustomItem, CustomItemFull, normal_filter, Unit,
                  generate_custom_for_purchase, PurchaseStatus, create_custom, 
                  get_purchase_item_full_by_custom)
from .schema import NCustomItem


def make_import_apis(prefix, auth_decorator, dbapi,
                     jinja_env):
    app = Bottle()
    dbcontext = DBContext(dbapi.session)

    bind_dbapi_rest(prefix + '/purchase', dbapi, Purchase, app)
    bind_dbapi_rest(prefix + '/purchase_item', dbapi, PurchaseItem, app)
    bind_dbapi_rest(prefix + '/universal_prod', dbapi, UniversalProd, app)
    bind_dbapi_rest(prefix + '/declaredgood', dbapi, DeclaredGood, app)
    bind_dbapi_rest(prefix + '/custom_item', dbapi, CustomItem, app)

    @app.get(prefix + '/universal_prod_with_declared')
    @dbcontext
    @auth_decorator
    def get_universal_prod_with_declared():
        all_prod = dbapi.search(UniversalProd)
        all_declared = dbapi.search(DeclaredGood)

        return json_dumps({
            'prod': all_prod,
            'declared': all_declared
        })

    @app.get(prefix + '/purchase_filtered/<uid>')
    @dbcontext
    @auth_decorator
    def purchase_fitered(uid):
        purchase = get_purchase_full(dbapi, uid)
        map(normal_filter, purchase.items)
        total = sum(i.item.price_rmb * i.item.quantity for i in purchase.items)
        purchase.meta.total_rmb = total
        res = purchase.serialize()
        res['units'] = {x.uid: x for x in dbapi.search(Unit)} 
        return json_dumps(res)

    @app.get(prefix + '/purchase_full/<uid>')
    @dbcontext
    @auth_decorator
    def get_purchase_full_http(uid):
        res = get_purchase_full(dbapi, uid).serialize()
        res['units'] = {x.uid: x for x in dbapi.search(Unit)} 
        return json_dumps(res)

    @app.post(prefix + '/purchase_full')
    @dbcontext
    @auth_decorator
    def create_full_purchase():
        rows = json.loads(request.body.read())
        purchase = Purchase()
        purchase.timestamp = datetime.datetime.now()
        pid = dbapi.create(purchase)

        def make_item(r):
            return PurchaseItem(
                upi=r['prod']['upi'],
                quantity=Decimal(r['cant']),
                price_rmb=Decimal(r['price']),
                purchase_id=pid)

        items = map(make_item, rows)
        total = sum((r.price_rmb * r.quantity for r in items))
        dbapi.update(purchase, {'total_rmb': total})
        map(dbapi.create, items)
        return {'uid': pid}

    @app.put(prefix + '/purchase_full/<uid>')
    @dbcontext
    def update_purchase_full(uid):
        data = json.loads(request.body.read())
        print data
        # update meta
        updated = Purchase.deserialize(data['meta'])
        print updated.timestamp
        updated.last_edit_timestamp = datetime.datetime.now()
        dbapi.update_full(updated)

        to_create_item = map(PurchaseItem.deserialize, data.get('create_items', []))
        for pi in to_create_item:
            pi.purchase_id = uid
            dbapi.create(pi)
        to_delete_item = map(PurchaseItem.deserialize, data.get('delete_items', []))
        for pi in to_delete_item:
            dbapi.delete(pi)
        to_edit_item = map(PurchaseItem.deserialize, data.get('edit_items', []))
        for pi in to_edit_item:
            dbapi.update_full(pi)
        return {'status': 'success'}

    @app.get(prefix + '/custom_full/<uid>')
    @dbcontext
    def get_custom_full(uid):
        result = {'meta': dbapi.get(uid, Purchase),
                  'customs': get_custom_items_full(dbapi, uid),
                  'units': {x.uid: x for x in dbapi.search(Unit)}}
        return json_dumps(result)

    @app.put(prefix + '/custom_full/<uid>')
    @dbcontext
    def get_custom_full(uid):
        data = json.loads(request.body.read())
        groupings = defaultdict(list)
        for x in data['customs']:
            obj = CustomItemFull.deserialize(x)
            if 'grouping' in x['custom']:
                grouping = x['custom']['grouping']
                groupings[grouping].append(obj)
            if '_edited' in x['custom'] and x['custom']['_edited']:
                dbapi.update_full(obj.custom)
        for val in groupings.values():
            if len(val) < 2:
                continue
            first = val[0]
            fcustom = first.custom
            others = val[1:]
            price = min(x.custom.price_rmb for x in val)
            name = max((len(x.custom.display_name.strip()), x.custom.display_name) for x in val)[1]
            for other in others:
                fcustom.quantity += other.custom.quantity
                if not fcustom.box:
                    fcustom.box = 0
                fcustom.box += (other.custom.box or 0)
                first.purchase_items.extend(other.purchase_items)
                dbapi.delete(other.custom)
            fcustom.price_rmb = price
            fcustom.display_name = name
            dbapi.update_full(fcustom)
            for pitem in first.purchase_items:
                dbapi.update(pitem.item, {'custom_item_uid': fcustom.uid})
        return '{"status": "success"}'

    @app.post(prefix + '/split_custom_items')
    @dbcontext
    def split_custom_items():
        declared = {x.uid: x for x in dbapi.search(DeclaredGood)}
        units = {x.uid: x for x in dbapi.search(Unit)}
        obj = CustomItemFull.deserialize(json.loads(request.body.read()))
        new_customs = []
        pitems = get_purchase_item_full_by_custom(dbapi, obj.custom.uid)
        for x in pitems:
            c = create_custom(x, declared, units)
            uid = dbapi.create(c)
            dbapi.update(x.item, {'custom_item_uid': uid})
            new_customs.append(CustomItemFull(c, [x]))
        dbapi.delete(obj.custom)
        return json_dumps({'result': new_customs})

    @app.post(prefix + '/custom_full/purchase/<uid>')
    @dbcontext
    def post_create_custom(uid):
        purchase_meta = dbapi.get(uid, Purchase)
        if purchase_meta == PurchaseStatus.NEW:
            return '{"status": "not generated"}'
        dbapi.db_session.query(NCustomItem).filter_by(purchase_id=uid).delete()
        generate_custom_for_purchase(dbapi, uid)
        dbapi.update(purchase_meta, {'status': PurchaseStatus.CUSTOM})
        return '{"status": "success"}'

    @app.get(prefix + '/custom_invoice/<uid>')
    @dbcontext
    def get_custom_invoice(uid):
        meta = dbapi.get(uid, Purchase)
        customs = list(dbapi.search(CustomItem, purchase_id=uid))
        customs.sort(key=lambda x: x.box_code) 
        date_str = meta.timestamp.strftime('%Y %B %d')
        total = sum(item.quantity * item.price_rmb for item in customs)
        temp = jinja_env.get_template('import/custom_invoice.html')
        return temp.render(
            use_riyao=False, inv_id='0{}'.format(meta.uid), 
            custom_items=customs, total=total.quantize(Decimal('0.01')),
            meta=meta, date_str=date_str)

    @app.get(prefix + '/custom_plist/<uid>')
    @dbcontext
    def get_custom_invoice(uid):
        meta = dbapi.get(uid, Purchase)
        customs = list(dbapi.search(CustomItem, purchase_id=uid))
        customs.sort(key=lambda x: x.box_code) 
        date_str = meta.timestamp.strftime('%Y %B %d')
        temp = jinja_env.get_template('import/custom_plist.html')
        total_weight = 0
        for item in customs:
            if 'kilogram' in item.unit:
                item.weight = item.quantity
            else:
                item.weight = item.box * 30
            total_weight += item.weight
        return temp.render(
            use_riyao=False, inv_uid='0{}'.format(meta.uid),
            custom_items=customs, 
            total_weight=total_weight,
            meta=meta, date_str=date_str)

    @app.get(prefix + '/purchase_detailed/<uid>.html')
    @dbcontext
    def purchase_detailed(uid):
        unfiltered = request.query.get('lang', '') == 'zh'
        purchase = get_purchase_full(dbapi, uid)
        declared = {x.uid: x for x in dbapi.search(DeclaredGood)}
        for x in purchase.items:
            x.item.box_code = declared[x.prod_detail.declaring_id].box_code
        purchase.items = sorted(
            purchase.items, 
            key=lambda x: (x.item.box_code, x.prod_detail.providor_zh))
        if unfiltered:
            temp = jinja_env.get_template('import/purchase_zh.html')
        else:
            map(normal_filter, purchase.items)
            temp = jinja_env.get_template('import/purchase_detailed.html')
        return temp.render(meta=purchase.meta, 
                items=purchase.items, 
                units={x.uid: x for x in dbapi.search(Unit)})

    @app.get(prefix + '/unit')
    @dbcontext
    def get_all_units():
        return json_dumps({x.uid: x for x in dbapi.search(Unit)})

    @app.get(prefix + '/unit/<uid>')
    @dbcontext
    def get_unit(uid):
        return json_dumps(dbapi.get(uid, Unit))

    @app.post(prefix + '/unit')
    @dbcontext
    def create_unit():
        u = Unit.deserialize(json.loads(request.body.read()))
        key = dbapi.create(u)
        return json_dumps({'key': key})

    @app.put(prefix + '/unit/<uid>')
    @dbcontext
    def update_unit(uid):
        u = Unit(uid=uid)
        num = dbapi.update(u, json.loads(request.body.read()))
        return json_dumps({'updated': num})

    return app

