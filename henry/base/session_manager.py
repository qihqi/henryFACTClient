import traceback
from bottle import HTTPResponse


class SessionManager(object):

    def __init__(self, session_factory):
        self._session = None
        self._factory = session_factory

    def __enter__(self):
        self._session = self._factory()
        return self._session

    def __exit__(self, type_, value, stacktrace):
        if type_ is None:
            self._session.commit()
            self._session.close()
            return True
        else:
            if type_ is not HTTPResponse:
                traceback.print_exception(type_, value, stacktrace)
                self._session.rollback()
            else:
                self._session.commit()
            self._session.close()
            return False

    @property
    def session(self):
        return self._session


class DBContext(object):

    def __init__(self, sessionmanager):
        self.sm = sessionmanager

    # used as decorator
    def __call__(self, func):

        def wrapped(*args, **kwargs):
            with self.sm:
                return func(*args, **kwargs)
        return wrapped