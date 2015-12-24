import os
from bottle import Bottle, request, redirect
from sqlalchemy.exc import IntegrityError
import barcode
from decimal import Decimal

from henry.coreconfig import (dbcontext, auth_decorator,
                              storeapi, priceapi)
from henry.config import jinja_env, prodapi, imagefiles
from henry.dao.productos import Product
from henry.base.common import convert_to_cent

__author__ = 'han'

webprod = w = Bottle()


@w.get('/app/crear_producto')
@dbcontext
@auth_decorator
def create_prod_form(message=''):
    temp = jinja_env.get_template('prod/crear_producto.html')
    stores = storeapi.search()
    categorias = prodapi.category.search()
    return temp.render(almacenes=stores, categorias=categorias,
                       message=message)


@w.get('/app/ver_lista_precio')
@dbcontext
@auth_decorator
def ver_lista_precio():
    almacen_id = int(request.query.get('almacen_id', 1))
    prefix = request.query.get('prefix', None)
    if prefix:
        prods = priceapi.search(**{'nombre-prefix': prefix,
                                     'almacen_id': almacen_id})
    else:
        prods = []
    temp = jinja_env.get_template('prod/ver_lista_precio.html')
    return temp.render(
        prods=prods, stores=storeapi.search(), prefix=prefix,
        almacen_name=storeapi.get(almacen_id).nombre)


@w.post('/app/crear_producto')
@dbcontext
@auth_decorator
def create_prod():
    p = Product()
    p.codigo = request.forms.codigo
    p.nombre = request.forms.nombre
    p.categoria = request.forms.categoria

    precios = {}
    for alm in storeapi.search():
        p1 = request.forms.get('{}-precio1'.format(alm.almacen_id))
        p2 = request.forms.get('{}-precio2'.format(alm.almacen_id))
        thres = request.forms.get('{}-thres'.format(alm.almacen_id))
        if p1 and p2:
            p1 = convert_to_cent(p1)
            p2 = convert_to_cent(p2)
            precios[alm.almacen_id] = (p1, p2, thres)
    try:
        prodapi.create_product_full(p, precios)
        message = 'producto con codigo "{}" creado'.format(p.codigo)
    except IntegrityError:
        message = 'Producto con codigo {} ya existe'.format(p.codigo)

    return create_prod_form(message=message)


@w.get('/app/ver_producto_form')
@auth_decorator
def ver_producto_form():
    return jinja_env.get_template('ver_item.html').render(
        title='Ver Producto',
        baseurl='/app/producto',
        apiurl='/api/producto')


@w.get('/app/producto/<uid>')
@dbcontext
@auth_decorator
def ver_producto(uid):
    prod = prodapi.get_producto_full(uid)
    price_dict = {}
    for x in prod.precios:
        price_dict[x.almacen_id] = x
    prod.precios = price_dict
    temp = jinja_env.get_template('prod/producto.html')
    return temp.render(prod=prod, stores=storeapi.search())


@w.get('/app/producto')
@dbcontext
@auth_decorator
def buscar_producto_result():
    prefix = request.query.prefijo
    if prefix is None:
        redirect('/app/ver_producto_form')
    prods = prodapi.prod.search(**{'nombre-prefix': prefix})
    temp = jinja_env.get_template('prod/buscar_producto_result.html')
    return temp.render(prods=prods)


@w.get('/app/barcode_form')
@dbcontext
@auth_decorator
def barcode_form():
    msg = request.query.msg
    temp = jinja_env.get_template('prod/barcode_form.html')
    return temp.render(alms=prodapi.store.search(), msg=msg)


@w.get('/app/barcode')
@dbcontext
@auth_decorator
def get_barcode():
    prod_id = request.query.get('prod_id')
    almacen_id = request.query.get('almacen_id')
    quantity = int(request.query.get('quantity', 1))

    prod = priceapi.getone(prod_id=prod_id, almacen_id=almacen_id)

    if quantity > 1000:
        redirect('/app/barcode_form?msg=cantidad+muy+grande')

    if not prod:
        redirect('/app/barcode_form?msg=producto+no+existe')

    encoded_string = '{:03d}{:09d}'.format(quantity, prod.pid)
    bar = barcode.EAN13(encoded_string)
    filename = bar.ean + '.svg'
    path = imagefiles.make_fullpath(filename)
    if not os.path.exists(path):
        with open(path, 'w') as barcode_file:
            bar.write(barcode_file)
    url = '/app/img/{}'.format(filename)

    column = 5
    row = 9
    price = int(prod.precio1 * quantity * Decimal('1.12') + Decimal('0.5'))

    temp = jinja_env.get_template('prod/barcode.html')
    return temp.render(url=url, row=row, column=column, prodname=prod.nombre, price=price)

