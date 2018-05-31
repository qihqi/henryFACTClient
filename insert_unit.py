import sys
import json
from henry.base.serialization import json_dumps
from henry.importation.dao import Unit, ALL_UNITS
from coreapi import dbapi

with dbapi.session:
    for x in sys.stdin.readlines():
        u = Unit.deserialize(json.loads(x))
        dbapi.create(u)
