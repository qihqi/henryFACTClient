import bottle
from datetime import datetime
from bottle import request, Bottle
from henry.config import jinja_env, transapi, prodapi
from henry.layer2.productos import Transferencia, TransType

w = Bottle()

@w.get('/app/ingreso/<uid>')
def get_ingreso(uid):
    trans = transapi.get_doc(uid)
    if trans:
        temp = jinja_env.get_template('ingreso.html')
        return temp.render(ingreso=trans)


@w.get('/app/crear_ingreso')
def create_increase():
    return bottle.static_file('static/ingreso.html', root='.')


def parse_and_validate_ingress_params(quantities, prod_ids):
    result = []
    for cant, prod_id in zip(quantities, prod_ids):
        if cant and prod_ids:
            cant = int(cant)
            p = prodapi.get_producto(prod_id)
            if p is None:
                raise ValueError("Producto No existe")
            result.append((cant, prod_id, p.nombre))
    return result


@w.post('/app/crear_ingreso')
def post_crear_ingreso():
    bodega_id = request.forms.get('bodega_id')
    trans = Transferencia()
    trans.origin = None
    trans.dest = bodega_id
    trans.trans_type = TransType.INGRESS
    trans.timestamp = datetime.now()
    for cant, prod_id, nombre in parse_and_validate_ingress_params(
            quantities=request.forms.getlist('cant'),
            prod_ids=request.forms.getlist('codigo')):
        trans.add_item(cant, prod_id)

    trans = transapi.save(trans)
    return str(trans.uid)

