import datetime

import bottle
from bottle import request, Bottle, abort, redirect
from henry.config import jinja_env, transapi, prodapi
from henry.layer2.productos import Transferencia, TransType

w = Bottle()

@w.get('/app/ingreso/<uid>')
def get_ingreso(uid):
    trans = transapi.get_doc(uid)
    print trans.serialize()
    if trans:
        temp = jinja_env.get_template('ingreso.html')
        return temp.render(ingreso=trans)


@w.get('/app/crear_ingreso')
def create_increase():
    temp = jinja_env.get_template('crear_ingreso.html')
    bodegas = prodapi.get_bodegas()
    return temp.render(bodegas=bodegas, types=TransType.names)


@w.post('/app/crear_ingreso')
def post_crear_ingreso():
    trans = Transferencia()
    trans.dest = request.forms.get('dest')
    trans.origin = request.forms.get('origin')
    trans.trans_type = request.forms.get('type')
    trans.timestamp = datetime.datetime.now()
    for cant, prod_id in zip(
            request.forms.getlist('cant'),
            request.forms.getlist('codigo')):
        if not cant.strip() or not prod_id.strip():
            # skip empty lines
            continue

        try:
            cant = int(cant)
        except ValueError:
            abort(400, 'cantidad debe ser entero positivo')
        if cant < 0:
            abort(400, 'cantidad debe ser entero positivo')
        trans.add_item(cant, prod_id)
    try:
        trans = transapi.save(trans)
    except ValueError as e:
        abort(400, str(e))

    redirect('/app/ingreso/{}'.format(trans.uid))

