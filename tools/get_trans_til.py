from henry.config import sessionmanager
from henry.config import transapi, prodapi
from henry.dao.document import Transferencia
import requests
import datetime
ROOT = 'http://192.168.0.22/api/ingreso/{}'

def main():
    with sessionmanager as session:
        ids = []
        for x in transapi.search_metadata_by_date_range(
                datetime.date(2015, 7, 1), datetime.date(2015, 8, 1)):
                if x.trans_type == 'EXTERNA':
                    ids.append(x.uid)
        for x in ids:
            url = ROOT.format(x)
            content = requests.get(url).json()
            trans = Transferencia.deserialize(content)
            def get_value(t):
                prod = prodapi.get_producto(prod_id=t.prod.codigo, almacen_id=2)
                if prod is None:
                    return 0
                return t.cant * prod.precio1
            value = sum( (get_value(t) for t in trans.items))
            print x, value
main()
    

        
