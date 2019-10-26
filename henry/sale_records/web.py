import datetime
import json
from bottle import Bottle, request
from henry.base.common import parse_start_end_date
from henry.base.dbapi_rest import bind_dbapi_rest
from henry.base.serialization import json_dumps, parse_iso_date
from henry.base.session_manager import DBContext
from henry.dao.document import Status
from henry.product.dao import ProdItemGroup, InventoryMovement

from .dao import (
    client_sale_report,
    InvMovementMeta, InvMovementFull, Sale,
    get_sales_by_date_and_user, get_or_create_inventory_id, Inventory, Entity)
from .schema import NSale

__author__ = 'han'


def make_sale_records_api(prefix, auth_decorator, dbapi,
                          invmomanager, inventoryapi):
    app = Bottle()
    dbcontext = DBContext(dbapi.session)

    bind_dbapi_rest(prefix + '/entity', dbapi, Entity, app)

    @app.post(prefix + '/client_sale')
    @dbcontext
    @auth_decorator(0)
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
    @auth_decorator(0)
    def get_sales():
        start, end = parse_start_end_date(request.query)
        result = list(get_sales_by_date_and_user(dbapi, start, end))
        return json_dumps(result)

    @app.delete(prefix + '/client_sale')
    @dbcontext
    @auth_decorator(0)
    def delete_sale():
        content = Sale.deserialize(json.loads(request.body.read()))
        deleted = dbapi.db_session.query(NSale).filter_by(
            seller_codename=content.seller_codename, seller_inv_uid=content.seller_inv_uid
        ).update({'status': Status.DELETED})
        return {'deleted': deleted}

    @app.post(prefix + '/inv_movement_set')
    @dbcontext
    @auth_decorator(0)
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
    # expects [proditemgroup, inventoryMovement, codename]
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
