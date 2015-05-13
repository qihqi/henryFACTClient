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
    username = request.forms.get('username')
    password = request.forms.get('password')

    with sessionmanager as session:
        info = get_user_info(session, username)
        if info is None:
            return {'status': False, 'message': 'Usuario no encontrado'}
        if authenticate(username, password, info):
            session = request.environ.get('beaker.session')
            session['loginin'] = True
            session.save()
            # set session to beaker
            # return serialized info
            return {
                'status': True, 
                'last_factura': info.last_factura,
                'bodega_factura_id': info.bodega_factura_id,
            }
        return {'status': False, 'message': 'Clave equivocada'}



@app.get('/islogin')
def get_session():
    session = request.environ.get('beaker.session')
    if not session:
        print 'not session'
    return 'answer is ' + str('loginin' in session)
