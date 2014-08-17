from datetime import datetime
from bottle import request, Bottle
from henry.config import jinja_env, transapi
from henry.layer2.productos import Transferencia, TransType

w = Bottle()

@w.get('/app/crear_ingreso')
def create_increase():
    return bottle.static_file('static/ingreso.html', root='.')


@w.get('/app/ingreso/<uid>')
def get_ingreso(uid):
    trans = transapi.get_doc(uid)
    if trans:
        temp = jinja_env.get_template('ingreso.html')
        return temp.render(ingreso=trans)

@w.post('/app/crear_ingreso')
def post_crear_ingreso():
    bodega_id = request.forms.get('bodega_id')
    trans = Transferencia()
    trans.origin = None
    trans.dest = bodega_id
    trans.trans_type = TransType.INGRESS
    trans.timestamp = datetime.now()
    trans.items = [(cant, prod_id, bodega_id) for prod_id, cant in
                    zip(request.forms.getlist('codigo'),
                        request.forms.getlist('cant'))]

    trans = transapi.save(trans)
    return trans.uid

