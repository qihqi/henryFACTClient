from hashlib import sha1
from bottle import request, redirect, response, parse_auth
from henry.base.schema import NUsuario, NDjangoSession


def get_user_info(session, username):
    return session.query(NUsuario).filter_by(username=username).first()


def authenticate(password, userinfo):
    s = sha1()
    s.update(password)
    return s.hexdigest() == userinfo.password


def create_user_dict(userinfo):
    return {
        'status': True,
        'last_factura': userinfo.last_factura,
        'bodega_factura_id': userinfo.bodega_factura_id,
    }

class AuthDecorator:

    def __init__(self, redirect_url, db):
        self.redirect = redirect_url
        self.db = db

    def __call__(self, func):
        def wrapped(*args, **kwargs):
            print request.get_header('Authorization')
            if (self.is_logged_in_by_beaker()
                    or self.is_logged_in_by_django()
                    or self.is_auth_by_header()):
                return func(*args, **kwargs)
            else:
                response.status = 401
                response.set_header('www-authenticate', 'Basic realm="Henry"')
        return wrapped

    def is_auth_by_header(self):
        header = request.get_header('Authorization')
        if header is None:
            return False
        pair = parse_auth(header)
        if pair is None:
            return False
        user, passwd = pair
        userinfo = get_user_info(self.db.session, user)
        if userinfo is None:
            return False
        if authenticate(passwd, userinfo):
            beaker = request.environ.get('beaker.session')
            beaker['login_info'] = create_user_dict(userinfo)
            beaker.save()
            return True
        return False

    def is_logged_in_by_beaker(self):
        session = request.environ['beaker.session']
        if session is not None:
            return 'login_info' in session
        return False

    def is_logged_in_by_django(self):
        session_key = request.get_cookie('sessionid', None)
        if session_key is not None:
            with self.db as session:
                key = session.query(
                NDjangoSession).filter_by(
                session_key=session_key).first()
                if key is not None:
                    return True
        return False
