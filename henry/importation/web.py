from __future__ import print_function
from builtins import map
import json
import datetime
from decimal import Decimal

from bottle import Bottle, request

from henry.dao.document import Status
from henry.base.common import parse_start_end_date
from henry.base.dbapi_rest import bind_dbapi_rest
from henry.base.serialization import json_dumps, decode_str, parse_iso_date
from henry.base.session_manager import DBContext
from henry.sale_records.dao import InvMovementFull, get_or_create_inventory_id, InvMovementMeta, \
    get_sales_by_date_and_user, Sale, client_sale_report, Inventory
from henry.product.dao import ProdItemGroup, InventoryMovement
from henry.sale_records.schema import NSale
from .dao import (Purchase, PurchaseItem, UniversalProd, DeclaredGood,
                  get_purchase_full,
                  CustomItem, normal_filter, Unit)


def make_import_apis(prefix, auth_decorator, dbapi,
                     jinja_env, invmomanager, inventoryapi):
    app = Bottle()
    dbcontext = DBContext(dbapi.session)

    bind_dbapi_rest(prefix + '/purchase', dbapi, Purchase, app)
    bind_dbapi_rest(prefix + '/purchase_item', dbapi, PurchaseItem, app)
    bind_dbapi_rest(prefix + '/universal_prod', dbapi, UniversalProd, app)
    bind_dbapi_rest(prefix + '/declaredgood', dbapi, DeclaredGood, app)
    bind_dbapi_rest(prefix + '/custom_item', dbapi, CustomItem, app)

    @app.get(prefix + '/universal_prod_with_declared')
    @dbcontext
    @auth_decorator(0)
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
        list(map(normal_filter, purchase.items))
        total = sum(i.item.price_rmb * i.item.quantity for i in purchase.items)
        purchase.meta.total_rmb = total
        res = purchase.serialize()
        res['units'] = {x.uid: x for x in dbapi.search(Unit)}
        return json_dumps(res)

    @app.get(prefix + '/purchase_full/<uid>')
    @dbcontext
    @auth_decorator(0)
    def get_purchase_full_http(uid):
        res = get_purchase_full(dbapi, uid).serialize()
        res['units'] = {x.uid: x for x in dbapi.search(Unit)}
        return json_dumps(res)

    @app.post(prefix + '/purchase_full')
    @dbcontext
    @auth_decorator(0)
    def create_full_purchase():
        rows = json.loads(decode_str(request.body.read()))
        purchase = Purchase()
        purchase.timestamp = datetime.datetime.now()
        pid = dbapi.create(purchase)

        def make_item(r):
            return PurchaseItem(
                upi=r['prod']['upi'],
                quantity=Decimal(r['cant']),
                price_rmb=Decimal(r['price']),
                purchase_id=pid)

        items = list(map(make_item, rows))
        total = sum((r.price_rmb * r.quantity for r in items))
        dbapi.update(purchase, {'total_rmb': total})
        list(map(dbapi.create, items))
        return {'uid': pid}

    @app.put(prefix + '/purchase_full/<uid>')
    @dbcontext
    def update_purchase_full(uid):
        data = json.loads(decode_str(request.body.read()))
        print(data)
        # update meta
        updated = Purchase.deserialize(data['meta'])
        print(updated.timestamp)
        updated.last_edit_timestamp = datetime.datetime.now()
        dbapi.update_full(updated)

        to_create_item = list(
            map(PurchaseItem.deserialize, data.get('create_items', [])))
        for pi in to_create_item:
            pi.purchase_id = uid
            dbapi.create(pi)
        to_delete_item = list(
            map(PurchaseItem.deserialize, data.get('delete_items', [])))
        for pi in to_delete_item:
            dbapi.delete(pi)
        to_edit_item = list(map(PurchaseItem.deserialize,
                            data.get('edit_items', [])))
        for pi in to_edit_item:
            dbapi.update_full(pi)
        return {'status': 'success'}

    @app.get(prefix + '/custom_full/<uid>')
    @dbcontext
    @auth_decorator(0)
    def post_sale():
        content = Sale.deserialize(json.loads(decode_str(request.body.read())))
        if list(dbapi.search(
                Sale, seller_codename=content.seller_codename,
                seller_inv_uid=content.seller_inv_uid)):
            return {
                'status': 'failed',
                'reason': 'sale with the id already exists'}
        dbapi.create(content)
        return {'status': 'success'}

    @app.put(prefix + '/custom_full/<uid>')
    @dbcontext
    @auth_decorator(0)
    def get_sales():
        start, end = parse_start_end_date(request.query)
        result = list(get_sales_by_date_and_user(dbapi, start, end))
        return json_dumps(result)

    @app.post(prefix + '/split_custom_items')
    @dbcontext
    @auth_decorator(0)
    def delete_sale():
        content = Sale.deserialize(json.loads(decode_str(request.body.read())))
        deleted = dbapi.db_session.query(NSale).filter_by(
            seller_codename=content.seller_codename, seller_inv_uid=content.seller_inv_uid
        ).update({'status': Status.DELETED})
        return {'deleted': deleted}

    @app.post(prefix + '/custom_full/purchase/<uid>')
    @dbcontext
    @auth_decorator(0)
    def post_inv_movement_set():
        raw_inv = decode_str(request.body.read())
        inv_movement = InvMovementFull.deserialize(json.loads(raw_inv))
        meta = inv_movement.meta
        meta.origin = get_or_create_inventory_id(
            dbapi, meta.inventory_codename, meta.origin)
        meta.dest = get_or_create_inventory_id(
            dbapi, meta.inventory_codename, meta.dest)

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
        print(today, tomorrow)
        movements = list(dbapi.search(InvMovementMeta, **
                         {'timestamp-gte': today, 'timestamp-lte': tomorrow}))
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
        raw_data = json.loads(decode_str(request.body.read()))
        ig = ProdItemGroup.deserialize(raw_data[0])
        trans = list(map(InventoryMovement.deserialize, raw_data[1]))
        codename = raw_data[2]

        if dbapi.getone(ProdItemGroup, prod_id=ig.prod_id) is None:
            if dbapi.get(ig.uid, ProdItemGroup) is not None:
                #  prod_id does not exist but uid is used so we cannot create
                #  using the same uid
                ig.uid = None
            dbapi.create(ig)

        for i in trans:
            i.itemgroup_id = ig.uid
            if dbapi.getone(
                    Inventory,
                    entity_codename=codename,
                    external_id=i.from_inv_id) is None:
                # create new Inventory if none
                i.from_inv_id = get_or_create_inventory_id(
                    dbapi, codename, i.from_inv_id)
                i.to_inv_id = get_or_create_inventory_id(
                    dbapi, codename, i.to_inv_id)
                i.reference_id = codename + (i.reference_id or '')
            inventoryapi.save(i)

    return app
