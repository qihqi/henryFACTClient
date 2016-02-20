import json
from bottle import Bottle, request
from decimal import Decimal
import datetime
from henry.base.dbapi_rest import bind_dbapi_rest
from .dao import Purchase, PurchaseItem, UniversalProd, DeclaredGood, get_purchase_full
from henry.base.serialization import json_dumps
from henry.base.session_manager import DBContext


def make_import_apis(prefix, dbapi):
    app = Bottle()
    dbcontext = DBContext(dbapi.session)

    bind_dbapi_rest(prefix + '/purchase', dbapi, Purchase, app)
    bind_dbapi_rest(prefix + '/purchase_item', dbapi, PurchaseItem, app)
    bind_dbapi_rest(prefix + '/universal_prod', dbapi, UniversalProd, app)
    bind_dbapi_rest(prefix + '/declaredgood', dbapi, DeclaredGood, app)

    @app.get(prefix + '/universal_prod_with_declared')
    @dbcontext
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
    def get_purchase_full_http(uid):
        return json_dumps(get_purchase_full(dbapi, uid))

    @app.post(prefix + '/purchase_full')
    @dbcontext
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

    return app
