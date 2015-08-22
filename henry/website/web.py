from bottle import request, redirect, Bottle, static_file, response
import datetime
from henry import constants
from henry.schema.core import NUsuario
from henry.config import dbcontext, auth_decorator, jinja_env, clientapi, sessionmanager, prodapi, actionlogged
from henry.constants import IMAGE_PATH
from henry.dao import Client
from henry.dao.exceptions import ItemAlreadyExists

webmain = w = Bottle()


@w.get('/app/img/<rest:path>')
@dbcontext
@auth_decorator
def img(rest):
    if constants.ENV == 'test':
        return static_file(rest, root=IMAGE_PATH)
    else:
        response.set_header('X-Accel-Redirect', '/image/{}'.format(rest))


@w.get('/app')
@dbcontext
@auth_decorator
def index():
    return jinja_env.get_template('base.html').render()


@w.get('/app/cliente/<id>')
@dbcontext
@auth_decorator
def modificar_cliente_form(id, message=None):
    client = clientapi.get(id)
    if client is None:
        message = 'Cliente {} no encontrado'.format(id)
    temp = jinja_env.get_template('crear_cliente.html')
    return temp.render(client=client, message=message, action='/app/modificar_cliente',
                       button_text='Modificar')

@w.post('/app/modificar_cliente')
@dbcontext
@auth_decorator
def modificar_cliente():
    clientid = request.forms.codigo
    clientapi.update(clientid, request.forms)
    redirect('/app/cliente/{}'.format(clientid))


@w.get('/app/cliente')
@dbcontext
@auth_decorator
def search_cliente_result():
    prefix = request.query.prefijo
    clientes = list(clientapi.search(prefix))
    temp = jinja_env.get_template('search_cliente_result.html')
    return temp.render(clientes=clientes)


@w.post('/app/crear_cliente')
@dbcontext
@auth_decorator
def crear_cliente():
    cliente = Client.deserialize(request.forms)
    cliente.cliente_desde = datetime.date.today()
    try:
        clientapi.create(cliente)
    except ItemAlreadyExists:
        return crear_cliente_form('Cliente con codigo {} ya existe'.format(cliente.codigo))
    return crear_cliente_form('Cliente {} {} creado'.format(cliente.apellidos, cliente.nombres))


@w.get('/app/secuencia')
@dbcontext
@auth_decorator
def get_secuencia():
    users = list(sessionmanager.session.query(NUsuario))
    temp = jinja_env.get_template('secuencia.html')
    store_dict = {s.almacen_id: s.nombre for s in prodapi.get_stores()}
    store_dict[-1] = 'Ninguno'
    return temp.render(users=users, stores=store_dict)


@w.post('/app/secuencia')
@dbcontext
@auth_decorator
@actionlogged
def post_secuencia():
    username = request.forms.usuario
    seq = request.forms.secuencia
    sessionmanager.session.query(NUsuario).filter_by(
        username=username).update({'last_factura': seq})
    redirect('/app/secuencia')


@w.get('/app/ver_cliente')
@dbcontext
@auth_decorator
def ver_cliente():
    temp = jinja_env.get_template('ver_item.html')
    return temp.render(title='Ver Cliente', baseurl='/app/cliente',
                       apiurl='/api/cliente')


@w.get('/app/crear_cliente')
@dbcontext
@auth_decorator
def crear_cliente_form(message=None):
    temp = jinja_env.get_template('crear_cliente.html')
    return temp.render(client=None, message=message, action='/app/crear_cliente',
                       button_text='Crear')
