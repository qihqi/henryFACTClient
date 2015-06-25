import bottle
from bottle import request

from henry.config import sessionmanager, dbcontext, auth_decorator
from henry.base.auth import create_user_dict, get_user_info, authenticate

app = bottle.Bottle()


@app.post('/api/authenticate')
def post_authenticate():
    beaker = request.environ.get('beaker.session')
    login_info = beaker.get('login_info')
    if login_info is not None:  # user is already logged in
        return login_info

    username = request.forms.get('username')
    password = request.forms.get('password')
    with sessionmanager as session:
        info = get_user_info(session, username)
        if info is None:
            return {'status': False, 'message': 'Usuario no encontrado'}
        if authenticate(password, info):
            data = create_user_dict(info)
            beaker['login_info'] = data
            beaker.save()
            return data
        return {'status': False, 'message': 'Clave equivocada'}


@app.get('/api/islogin')
@dbcontext
@auth_decorator
def get_session():
    session = request.environ.get('beaker.session')
    login_info = session.get('login_info')
    print session
    if login_info is not None:  # user is already logged in
        return login_info
    return {'message': 'Not logged in', 'status': False}
