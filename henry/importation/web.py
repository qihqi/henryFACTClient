import json
import datetime
from decimal import Decimal

from bottle import Bottle, request
from henry.base.common import parse_start_end_date
from henry.base.dbapi_rest import bind_dbapi_rest
from henry.base.serialization import json_dumps
from henry.base.session_manager import DBContext
from henry.dao.document import Status
from henry.product.dao import ProdItemGroup

from .schema import NSale
from .dao import (Purchase, PurchaseItem, UniversalProd, DeclaredGood,
                  get_purchase_full, Sale, Entity, InvMovementFull,
                  InvMovementMeta, Inventory, get_sales_by_date_and_user)


def make_import_apis(prefix, auth_decorator, dbapi, invmomanager):
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

    @app.get(prefix + '/purchase_full/<uid>')
    @dbcontext
    @auth_decorator
    def get_purchase_full_http(uid):
        return json_dumps(get_purchase_full(dbapi, uid))

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

    @app.post(prefix + '/client_sale')
    @dbcontext
    @auth_decorator
    def post_sale():
        content = Sale.deserialize(json.loads(request.body.read()))
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
        # rewrite origin/dest
        def get_or_create(codename, ext_uid):
            if ext_uid == -1:
                return -1
            inv = dbapi.getone(Inventory, entity_codename=codename, external_id=ext_uid)
            if not inv:
                inv = Inventory(entity_codename=codename, external_id=ext_uid)
                dbapi.create(inv)
            return inv.uid
        meta.origin = get_or_create(meta.inventory_codename, meta.origin)
        meta.dest = get_or_create(meta.inventory_codename, meta.dest)

        if dbapi.search(InvMovementMeta,
                        inventory_codename=meta.inventory_codename,
                        inventory_docid=meta.inventory_docid,
                        trans_type=meta.trans_type):
            #already exists
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

    @app.get(prefix + '/inv_movement')
    @dbcontext
    def last_inv_movements():
        today = datetime.date.today()
        movements = dbapi.search(InvMovementMeta, **{'timestamp-gte': today})
        return json_dumps({'result': movements})

    return app
