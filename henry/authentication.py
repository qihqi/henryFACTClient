import sha
import bottle
from bottle import request
from henry.constants import CONN_STRING
from henry.layer1.schema import NUsuario
from henry.config import sessionmanager

app = bottle.Bottle() 

def authenticate(username, password, userinfo):
    s = sha.new(password)
    return s.hexdigest() == userinfo.password


def get_user_info(session, username):
    return session.query(NUsuario).filter_by(username=username).first()


@app.post('/api/authenticate')
def post_authenticate():
    beaker = request.environ.get('beaker.session')
    login_info = beaker.get('login_info')
    if login_info is not None: # user is already logged in
        return login_info

    username = request.forms.get('username')
    password = request.forms.get('password')
    with sessionmanager as session:
        info = get_user_info(session, username)
        if info is None:
            return {'status': False, 'message': 'Usuario no encontrado'}
        if authenticate(username, password, info):
            data = {
                'status': True, 
                'last_factura': info.last_factura,
                'bodega_factura_id': info.bodega_factura_id,
            }
            beaker['login_info'] = data
            beaker.save()
            return data
        return {'status': False, 'message': 'Clave equivocada'}



@app.get('/islogin')
def get_session():
    session = request.environ.get('beaker.session')
    login_info = session.get('login_info')
    if login_info is not None: # user is already logged in
        return login_info
    return {'message': 'Not logged in', 'status': False}
