from henry.config import *
from henry.schema.legacy import NTransform

with sessionmanager as session:
    reglas = list(session.query(NTransform))
    for x in reglas:
        if x.multiplier > 10:
            print prodapi.get_producto(x.origin_id).serialize()


