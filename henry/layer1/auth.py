from bottle import request, redirect
from henry.layer1.schema import NDjangoSession

def is_logged_in_by_django(request):
    session_key = request.get_cookie('sessionid', None)
    if session_key is not None:
        key = self.db.session.query(
        NDjangoSession).filter_by(
        session_key=session_key).first()
        return key is not None
    return False


def is_logged_in_by_beaker(request):
    session = request.environ['beaker.session']
    if session is not None:
        return 'loginin' in session
    return False

real_auth = (lambda r: is_logged_in_by_beaker(r) and
                       is_logged_in_by_beaker(r))
