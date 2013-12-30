from sqlalchemy import create_engine
import sys
import time

def timed(ostream):
    def inner(f):
        def ff(*args, **kwargs):
            start = time.time()
            f(*args, **kwargs)
            end = time.time()
            printd = '%s : %f\n' % (f.__name__, end - start)
            ostream.write(printd)
        return ff
    return inner

