import datetime
from decimal import Decimal
from bottle import Bottle, request, abort

from henry.base.serialization import json_dumps, json_loads, SerializableMixin
from henry.schema.inventory import NInventoryRevision, NInventoryRevisionItem
from henry.schema.core import NNota, NUsuario
from henry.config import (transapi, dbcontext, prodapi, clientapi,
                          invapi, auth_decorator, sessionmanager,
                          actionlogged, transactionapi, revisionapi)
from henry.dao import Invoice, Transferencia, Transaction

napi = Bottle()

@napi.get('/api/nota')
@dbcontext
@actionlogged
def get_invoice_by_date():
    start = request.query.get('start_date')
    end = request.query.get('end_date')
    if start is None or end is None:
        abort(400, 'invalid input')
    datestrp = datetime.datetime.strptime
    start_date = datestrp(start, "%Y-%m-%d")
    end_date = datestrp(end, "%Y-%m-%d")
    status = request.query.get('status')
    result = invapi.search_metadata_by_date_range(start_date, end_date, status)
    return json_dumps(list(result))



# ################# INGRESO ###########################3
@napi.post('/api/ingreso')
@dbcontext
@auth_decorator
@actionlogged
def crear_ingreso():
    json_content = request.body.read()
    json_dict = json_loads(json_content)
    ingreso = Transferencia.deserialize(json_dict)
    ingreso = transapi.save(ingreso)
    return {'codigo': ingreso.meta.uid}


@napi.put('/api/ingreso/<ingreso_id>')
@dbcontext
@auth_decorator
@actionlogged
def postear_ingreso(ingreso_id):
    trans = transapi.get_doc(ingreso_id)
    transapi.commit(trans)
    return {'status': trans.meta.status}


@napi.delete('/api/ingreso/<ingreso_id>')
@dbcontext
@actionlogged
def delete_ingreso(ingreso_id):
    trans = transapi.get_doc(ingreso_id)
    transapi.delete(trans)
    return {'status': trans.meta.status}


@napi.get('/api/ingreso/<ingreso_id>')
@dbcontext
@actionlogged
def get_ingreso(ingreso_id):
    ing = transapi.get_doc(ingreso_id)
    if ing is None:
        abort(404, 'Ingreso No encontrada')
        return
    return json_dumps(ing.serialize())


@napi.put('/api/revision/<rid>')
@dbcontext
@auth_decorator
@actionlogged
def put_revision(rid):
    if revisionapi.commit(rid):
        return {'status': 'AJUSTADO'}
    abort(404)
