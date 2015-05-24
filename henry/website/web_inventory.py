import datetime

from bottle import request, Bottle, abort, redirect
from henry.config import jinja_env, transapi, prodapi
from henry.layer2.productos import (TransType, Metadata, Product)
from henry.layer2.documents import DocumentCreationRequest
from henry.layer1.schema import NCategory
from henry.config import dbcontext, auth_decorator

w = Bottle()
web_inventory_webapp = w


@w.get('/app/ingreso/<uid>')
@dbcontext
@auth_decorator
def get_ingreso(uid):
    trans = transapi.get_doc(uid)
    bodegas = {x.id: x.nombre for x in prodapi.get_bodegas()}
    if trans:
        print trans.serialize()
        temp = jinja_env.get_template('ingreso.html')
        return temp.render(ingreso=trans, bodega_mapping=bodegas)
    else:
        return 'Documento con codigo {} no existe'.format(uid)


@w.get('/app/crear_ingreso')
@dbcontext
@auth_decorator
def crear_ingreso():
    temp = jinja_env.get_template('crear_ingreso.html')
    bodegas = prodapi.get_bodegas()
    return temp.render(bodegas=bodegas, types=TransType.names)


@w.post('/app/crear_ingreso')
@dbcontext
@auth_decorator
def post_crear_ingreso():
    meta = Metadata()
    meta.dest = int(request.forms.get('dest'))
    meta.origin = int(request.forms.get('origin'))
    meta.meta_type = request.forms.get('meta_type')
    meta.trans_type = request.forms.get('trans_type')
    meta.timestamp = datetime.datetime.now()
    trans = DocumentCreationRequest(meta)
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
        trans.add(prod_id, cant)
    try:
        transferencia = transapi.save(trans)
    except ValueError as e:
        abort(400, str(e))

    redirect('/app/ingreso/{}'.format(transferencia.meta.uid))


@w.get('/app/crear_producto')
@dbcontext
@auth_decorator
def create_prod_form():
    temp = jinja_env.get_template('crear_producto.html')
    stores = prodapi.get_stores()
    categorias = prodapi.get_category()
    return temp.render(almacenes=stores, categorias=categorias)


@w.post('/app/crear_producto')
@dbcontext
@auth_decorator
def create_prod_form():
    print request.forms.__dict__

    p = Product()
    p.codigo = request.forms.codigo
    p.nombre = request.forms.nombre
    p.categoria = request.forms.categoria

    precios = {}
    for alm in prodapi.get_stores():
        p1 = request.forms.get('{}-precio1'.format(alm.almacen_id))
        p2 = request.forms.get('{}-precio2'.format(alm.almacen_id))
        thres = request.forms.get('{}-thres'.format(alm.almacen_id))
        precios[alm.almacen_id] = (p1, p2, thres)

    prodapi.create_product(p, precios)
    redirect('/app/crear_producto')







