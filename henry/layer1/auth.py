from bottle import request, redirect
from henry.layer1.schema import NDjangoSession

class AuthDecorator(object):

    def __init__(self, db, redirect_url):
        self.db = db
        self.redirect_url = redirect_url

    def __call__(self, func):
        def inner(*args, **kwargs):
            session_key = request.get_cookie('session_id', None)
            if session_key is not None:
                key = self.db.session.query(
                    NDjangoSession).filter_by(
                    session_key=session_key).first()
                if key is not None:
                    return func(*args, **kwargs)
            redirect(self.redirect_url)
        return inner
