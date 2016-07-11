from collections import defaultdict
import json
import datetime
from decimal import Decimal

from bottle import Bottle, request
from henry.base.common import parse_start_end_date
from henry.base.dbapi_rest import bind_dbapi_rest
from henry.base.serialization import json_dumps, parse_iso_date
from henry.base.session_manager import DBContext
from henry.dao.document import Status
from henry.product.dao import ProdItemGroup, InventoryMovement
from sqlalchemy import func

from .schema import NSale
from .dao import (Purchase, PurchaseItem, UniversalProd, DeclaredGood,
                  get_purchase_full, Sale, Entity, InvMovementFull,
                  InvMovementMeta, Inventory, get_sales_by_date_and_user, get_or_create_inventory_id,
                  client_sale_report, ALL_UNITS, get_custom_items_full, CustomItem, CustomItemFull, normal_filter)


def make_import_apis(prefix, auth_decorator, dbapi,
                     invmomanager, inventoryapi, jinja_env):
    app = Bottle()
    dbcontext = DBContext(dbapi.session)

    bind_dbapi_rest(prefix + '/purchase', dbapi, Purchase, app)
    bind_dbapi_rest(prefix + '/purchase_item', dbapi, PurchaseItem, app)
    bind_dbapi_rest(prefix + '/universal_prod', dbapi, UniversalProd, app)
    bind_dbapi_rest(prefix + '/declaredgood', dbapi, DeclaredGood, app)
    bind_dbapi_rest(prefix + '/entity', dbapi, Entity, app)

    @app.get(prefix + '/universal_prod_with_declared')
    @dbcontext
    @auth_decorator
    def get_universal_prod_with_declared():
        all_prod = dbapi.search(UniversalProd)
        all_declared = dbapi.search(DeclaredGood)
        all_declared_map = {x.uid: x for x in all_declared}

        def join_declared(x):
            declared = x.declaring_id
            x = x.serialize()
            if declared in all_declared_map:
                x['declared_name'] = all_declared_map[declared].display_name
            return x

        return json_dumps({
            'prod': map(join_declared, all_prod),
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
        res['units'] = ALL_UNITS
        return json_dumps(res)

    @app.get(prefix + '/purchase_full/<uid>')
    @dbcontext
    @auth_decorator
    def get_purchase_full_http(uid):
        res = get_purchase_full(dbapi, uid).serialize()
        res['units'] = ALL_UNITS
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
                  'units': ALL_UNITS}
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

    @app.get(prefix + '/custom_invoice/<uid>')
    @dbcontext
    def get_custom_invoice(uid):
        meta = dbapi.get(uid, Purchase)
        customs = list(dbapi.search(CustomItem, purchase_id=uid))
        date_str = meta.timestamp.strftime('%Y %B %d')
        total = sum(item.quantity * item.price_rmb for item in customs)
        temp = jinja_env.get_template('import/custom_invoice.html')
        return temp.render(
            custom_items=customs, total=total.quantize(Decimal('0.01')),
            meta=meta, date_str=date_str)

    @app.get(prefix + '/custom_plist/<uid>')
    @dbcontext
    def get_custom_invoice(uid):
        meta = dbapi.get(uid, Purchase)
        customs = list(dbapi.search(CustomItem, purchase_id=uid))
        date_str = meta.timestamp.strftime('%Y %B %d')
        temp = jinja_env.get_template('import/custom_plist.html')
        total_box = 0
        total_weight = 0
        for item in customs:
            pass
        return temp.render(
            custom_items=customs, total_box=total_box,
            total_weight=total_weight,
            meta=meta, date_str=date_str)

    @app.get(prefix + '/purchase_detailed/<uid>.html')
    @dbcontext
    def purchase_detailed(uid):
        unfiltered = request.query.get('lang', '') == 'zh'
        purchase = get_purchase_full(dbapi, uid)
        temp = jinja_env.get_template('import/purchase_detailed.html')
        if unfiltered:
            temp = jinja_env.get_template('import/purchase_zh.html')
        else:
            map(normal_filter, purchase.items)
            temp = jinja_env.get_template('import/purchase_detailed.html')
        return temp.render(meta=purchase.meta, items=purchase.items, units=ALL_UNITS)

    @app.get(prefix + '/unit')
    @dbcontext
    def get_all_units():
        return json_dumps(ALL_UNITS)

    @app.get(prefix + '/unit/<uid>')
    @dbcontext
    def get_unit(uid):
        return json_dumps(ALL_UNITS[uid])

    @app.post(prefix + '/client_sale')
    @dbcontext
    @auth_decorator
    def post_sale():
        content = Sale.deserialize(json.loads(request.body.read()))
        if list(dbapi.search(
                Sale, seller_codename=content.seller_codename,
                seller_inv_uid=content.seller_inv_uid)):
            return {'status': 'failed', 'reason': 'sale with the id already exists'}
        dbapi.create(content)
        return {'status': 'success'}

    @app.get(prefix + '/client_sale')
    @dbcontext
    @auth_decorator
    def get_sales():
        start, end = parse_start_end_date(request.query)
        result = list(get_sales_by_date_and_user(dbapi, start, end))
        return json_dumps(result)

    @app.delete(prefix + '/client_sale')
    @dbcontext
    @auth_decorator
    def delete_sale():
        content = Sale.deserialize(json.loads(request.body.read()))
        deleted = dbapi.db_session.query(NSale).filter_by(
            seller_codename=content.seller_codename, seller_inv_uid=content.seller_inv_uid
        ).update({'status': Status.DELETED})
        return {'deleted': deleted}

    @app.post(prefix + '/inv_movement_set')
    @dbcontext
    @auth_decorator
    def post_inv_movement_set():
        raw_inv = request.body.read()
        inv_movement = InvMovementFull.deserialize(json.loads(raw_inv))
        meta = inv_movement.meta
        meta.origin = get_or_create_inventory_id(dbapi, meta.inventory_codename, meta.origin)
        meta.dest = get_or_create_inventory_id(dbapi, meta.inventory_codename, meta.dest)

        if list(dbapi.search(InvMovementMeta,
                             inventory_codename=meta.inventory_codename,
                             inventory_docid=meta.inventory_docid,
                             trans_type=meta.trans_type)):
            # already exists
            return {'created': 0, 'reason': 'already exists'}
        for igcant in inv_movement.items:
            prod_id = igcant.itemgroup.prod_id
            ig_real = dbapi.getone(ProdItemGroup, prod_id=prod_id)
            # itemgroup does not exist, create
            if not ig_real:
                dbapi.create(igcant.itemgroup)
            else:  # replace itemgroup as the itemgroup id might be distinct
                igcant.itemgroup = ig_real
        inv_movement = invmomanager.create(inv_movement)
        return {'created': inv_movement.meta.uid}

    @app.get(prefix + '/inv_movement/<day>')
    @dbcontext
    def last_inv_movements(day):
        today = parse_iso_date(day)
        tomorrow = today + datetime.timedelta(days=1)
        print today, tomorrow
        movements = list(dbapi.search(InvMovementMeta, **{'timestamp-gte': today, 'timestamp-lte': tomorrow}))
        return json_dumps({'result': movements})

    @app.get(prefix + '/sales_report')
    @dbcontext
    def get_sales_report():
        start, end = parse_start_end_date(request.query)
        sales_by_date = list(client_sale_report(dbapi, start, end))
        return json_dumps({'result': sales_by_date})

    # @app.post(prefix + '/raw_inv_movement')
    @dbcontext
    def post_raw_inv_movement():
        raw_data = json.loads(request.body.read())
        ig = ProdItemGroup.deserialize(raw_data[0])
        trans = map(InventoryMovement.deserialize, raw_data[1])
        codename = raw_data[2]

        if dbapi.getone(ProdItemGroup, prod_id=ig.prod_id) is None:
            if dbapi.get(ig.uid, ProdItemGroup) is not None:
                #  prod_id does not exist but uid is used so we cannot create
                #  using the same uid
                ig.uid = None
            dbapi.create(ig)

        for i in trans:
            i.itemgroup_id = ig.uid
            if dbapi.getone(Inventory, entity_codename=codename, external_id=i.from_inv_id) is None:
                # create new Inventory if none
                i.from_inv_id = get_or_create_inventory_id(dbapi, codename, i.from_inv_id)
                i.to_inv_id = get_or_create_inventory_id(dbapi, codename, i.to_inv_id)
                i.reference_id = codename + (i.reference_id or '')
            inventoryapi.save(i)

    return app

