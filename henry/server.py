import sys
import os
import bottle

from bottle import run, request
from bottle import HTTPError

from henry.bodega_api import bodega_api_app

app = bottle.Bottle()

def main():
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    from henry.layer1.schema import Base
    #setup_testdata()
    #print get_cliente_by_id('NA')
  #  print json.dumps(Venta.get(86590).serialize(), cls=ModelEncoder)
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    app.merge(bodega_api_app)
    run(app, host=host, debug=True, port=8080)
    return 'http://localhost:8080'


if __name__ == '__main__':
    main()



