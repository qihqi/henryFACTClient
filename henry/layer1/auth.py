from bottle import request, redirect
from henry.layer1.schema import NDjangoSession


class AuthDecorator:

    def __init__(self, redirect_url, db):
        self.redirect = redirect_url
        self.db = db

    def __call__(self, func):
        def wrapped(*args, **kwargs):
            if self.is_logged_in_by_beaker() or self.is_logged_in_by_django():
                return func(*args, **kwargs)
            else:
                redirect(self.redirect)
        return wrapped

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

    def is_logged_in_by_beaker(self):
        session = request.environ['beaker.session']
        if session is not None:
            return 'login_info' in session
        return False
                
               

