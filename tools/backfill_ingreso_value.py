import requests

from henry.config import itemgroupapi
from henry.coreconfig import sessionmanager
from henry.inventory.dao import Transferencia
from henry.inventory.schema import NTransferencia

__author__ = 'han'

def get_value(trans):
    def pr(prod):
        if getattr(prod, 'base_price_usd', None):
            return prod.base_price_usd
        itemgroup = itemgroupapi.search(prod_id=prod.prod_id)
        if not itemgroup or not itemgroup[0].base_price_usd:
            print 'codigo ', prod.prod_id, 'not found'
            return 0
        return itemgroup[0].base_price_usd
    return sum((pr(i.prod) * i.cant for i in trans.items))


def main():
    with sessionmanager as session:
        all_trans = session.query(NTransferencia)
        for t in all_trans:
            content = requests.get('http://192.168.0.22/app/api/ingreso/{}'.format(t.id))
            transfer = Transferencia.deserialize(content.json())
            value = get_value(transfer)
            t.value = value
        session.commit()


if __name__ == '__main__':
    main()
