
class DBContext(object):

    def __init__(self, sessionmanager):
        self.sm = sessionmanager

    # used as decorator
    def __call__(self, func):
        
        def wrapped(*args, **kwargs):
            with self.sm:
                return func(*args, **kwargs)
        return wrapped
            

