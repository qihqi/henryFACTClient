from bottle import Bottle, request
from henry.config import dbcontext, auth_decorator, prodapi, jinja_env

w = Bottle()

@w.get('/app/pricelist')
@dbcontext
@auth_decorator
def get_price_list():
    almacen_id = request.query.get('almacen_id')
    prefix = request.query.get('prefix')
    if not prefix:
        prefix = ''
    if almacen_id is None:
        abort(400, 'input almacen_id')
    all = prodapi.search_producto(prefix=prefix, almacen_id=almacen_id)
    temp = jinja_env.get_template('buscar_precios.html')
    return temp.render(prods=all)
