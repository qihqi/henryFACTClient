#!/usr/bin/env python
import traceback

from henry.background_sync.worker import make_worker_thread, ForwardRequestProcessor
from henry.base.dbapi import DBApiGeneric
from henry.constants import ZEROMQ_PORT, REMOTE_URL, REMOTE_USER, REMOTE_PASS, CODENAME
from henry.coreconfig import sessionmanager

dbapi = DBApiGeneric(sessionmanager)
processor = ForwardRequestProcessor(dbapi, REMOTE_URL, (REMOTE_USER, REMOTE_PASS), CODENAME)
f = make_worker_thread(ZEROMQ_PORT, processor)

def main():
    while True:
        try:
            f()
        except KeyboardInterrupt:
            raise
        except SystemExit:
            print 'Exiting'
        except:
            traceback.print_exc()

if __name__ == '__main__':
    main()
