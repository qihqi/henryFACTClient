import sys
import os

from bottle import run, static_file, Bottle

from henry.bodega_api import bodega_api_app
from henry.website.web_inventory import web_inventory_webapp
from henry.website.accounting import accounting_webapp


app = Bottle()


@app.get('/static/<rest:path>')
def static(rest):
    return static_file(rest, root='./static/')


app.merge(bodega_api_app)
app.merge(web_inventory_webapp)
app.merge(accounting_webapp)
def main():
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    from henry.layer1.schema import Base
    from henry.config import engine
    Base.metadata.create_all(engine)
    #setup_testdata()
    #print get_cliente_by_id('NA')
  #  print json.dumps(Venta.get(86590).serialize(), cls=ModelEncoder)
    host = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
    run(app, host=host, debug=True, port=8080)
    return 'http://localhost:8080'


if __name__ == '__main__':
    main()
