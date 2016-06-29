from henry.config import sessionmanager
from henry.schema.core import NPriceList
from henry.inventory.schema import NContenido

with sessionmanager as session:
    pricelist = session.query(NPriceList, NContenido).filter(
            NPriceList.upi == NContenido.id)
    for p, c in pricelist:
        c.inactivo = False
