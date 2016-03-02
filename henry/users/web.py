"""
This has handlers for pages regarding users and client
"""
import datetime
from bottle import Bottle, request, redirect, abort
from henry.base.auth import get_user_info, authenticate, create_user_dict

from henry.base.dbapi import dbmix
from henry.base.dbapi_rest import bind_dbapi_rest
from henry.base.serialization import json_dumps
from henry.base.session_manager import DBContext
from henry.dao.exceptions import ItemAlreadyExists
from henry.product.dao import Store

from .schema import NUsuario, NCliente

User = dbmix(NUsuario)


class Client(dbmix(NCliente)):

    @property
    def fullname(self):
        nombres = self.nombres
        if not nombres:
            nombres = ''
        apellidos = self.apellidos
        if not apellidos:
            apellidos = ''
        return apellidos + ' ' + nombres


def make_client_coreapi(url_prefix, dbapi, actionlogged):

    api = Bottle()
    dbcontext = DBContext(dbapi.session)

    @api.get(url_prefix + '/cliente/<codigo>')
    @dbcontext
    @actionlogged
    def get_cliente(codigo):
        client = dbapi.get(codigo, Client)
        if client is None:
            abort(404, 'cliente no encontrado')
        return json_dumps(client.serialize())

    @api.get(url_prefix + '/cliente')
    @dbcontext
    @actionlogged
    def search_client():
        prefijo = request.query.prefijo
        if prefijo:
            return json_dumps(list(
                dbapi.search(Client, **{'apellidos-prefix': prefijo})))
        abort(400)

    @api.post(url_prefix + '/authenticate')
    def post_authenticate():
        beaker = request.environ.get('beaker.session')
        login_info = beaker.get('login_info')
        if login_info is not None:  # user is already logged in
            return login_info

        username = request.forms.get('username')
        password = request.forms.get('password')
        with dbapi.session as session:
            info = get_user_info(session, username)
            if info is None:
                return {'status': False, 'message': 'Usuario no encontrado'}
            if authenticate(password, info):
                data = create_user_dict(info)
                beaker['login_info'] = data
                beaker.save()
                return data
            return {'status': False, 'message': 'Clave equivocada'}

    return api

def make_wsgi_app(dbcontext, auth_decorator, jinja_env, dbapi, actionlogged):
    w = Bottle()

    # bind apis
    bind_dbapi_rest('/app/api/client', dbapi, Client, w)
    bind_dbapi_rest('/app/api/user', dbapi, User, w)

    @w.get('/app/cliente/<id>')
    @dbcontext
    @auth_decorator
    def modificar_cliente_form(id, message=None):
        client = dbapi.get(id, Client)
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
        client = Client(codigo=clientid)
        dbapi.update(client, request.forms)
        redirect('/app/cliente/{}'.format(clientid))

    @w.get('/app/cliente')
    @dbcontext
    @auth_decorator
    def search_cliente_result():
        prefix = request.query.prefijo
        clientes = list(dbapi.search(Client, **{'apellidos-prefix': prefix}))
        temp = jinja_env.get_template('search_cliente_result.html')
        return temp.render(clientes=clientes)

    @w.post('/app/crear_cliente')
    @dbcontext
    @auth_decorator
    def crear_cliente():
        cliente = Client.deserialize(request.forms)
        cliente.cliente_desde = datetime.date.today()
        try:
            dbapi.create(cliente)
            dbapi.db_session.commit()
        except ItemAlreadyExists:
            return crear_cliente_form('Cliente con codigo {} ya existe'.format(cliente.codigo))
        return crear_cliente_form('Cliente {} {} creado'.format(cliente.apellidos, cliente.nombres))

    @w.get('/app/secuencia')
    @dbcontext
    @auth_decorator
    def get_secuencia():
        users = dbapi.search(User)
        temp = jinja_env.get_template('secuencia.html')
        store_dict = {s.almacen_id: s.nombre for s in dbapi.search(Store)}
        store_dict[-1] = 'Ninguno'
        return temp.render(users=users, stores=store_dict)

    @w.post('/app/secuencia')
    @dbcontext
    @auth_decorator
    @actionlogged
    def post_secuencia():
        username = request.forms.usuario
        seq = request.forms.secuencia
        user = User(username=username)
        dbapi.update(user, {'last_factura': seq})
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

    bind_dbapi_rest('/app/api/client', dbapi, Client, w)
    return w
