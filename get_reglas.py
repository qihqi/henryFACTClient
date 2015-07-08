from henry.base.schema import *
from henry.config import *

with sessionmanager as session:
    reglas = list(session.query(NTransform))
    for x in reglas:
        if x.multiplier > 10:
            print prodapi.get_producto(x.origin_id).serialize()


