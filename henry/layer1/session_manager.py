class SessionManager(object):

    def __init__(self, session_factory):
        self._session = None
        self._factory = session_factory

    def __enter__(self):
        self._session = self._factory()
        return self._session

    def __exit__(self, type, value, traceback):
        if type is None:
            self._session.commit()
        else:
            print type, value, traceback
            self._session.rollback()
        return True

    @property
    def session(self):
        return self._session
