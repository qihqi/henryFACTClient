import sys
from decimal import Decimal
from henry.coreconfig import sessionmanager
from henry.config import prodapi
from henry.schema.prod import NItemGroup

def decode(line):
    try:
        return line.decode('utf8')
    except:
        return line.decode('latin1')

def main():
    codigos = set()
    with open(sys.argv[1]) as f:
        for line in f.readlines():
            realstring = decode(line)
            codigos.add(realstring.strip().upper())
    with sessionmanager as session:
        for x in codigos:
            prod = prodapi.prod.get(x)
            bigid = x + '+'
            price = prodapi.price.search(prod_id=bigid, almacen_id=2)
            if not price:
                price = prodapi.price.search(prod_id=x, almacen_id=2) 

            if price:
                price = price[0]
                baseprice = Decimal(price.precio2) / 100 / price.multiplicador
            else:
                baseprice = None
            item = NItemGroup(
                prod_id=x,
                name=prod.nombre,
                base_price_usd=baseprice)
            session.add(item)
        session.commit()
main()
