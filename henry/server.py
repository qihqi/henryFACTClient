import datetime
import sys
import os

from bottle import run, request, static_file, Bottle, HTTPError

from henry.bodega_api import bodega_api_app
from henry.website.web_inventory import w
from henry.config import sessionfactory
from henry.layer2.invoice import InvApiOld

app = Bottle()

@app.get('/static/<rest:path>')
def static(rest):
    return static_file(rest, root='./static/')


def main():
    sys.path.append(os.path.dirname(os.path.realpath(__file__)))
    from henry.layer1.schema import Base
    from henry.config import engine
    Base.metadata.create_all(engine)
    #setup_testdata()
    #print get_cliente_by_id('NA')
  #  print json.dumps(Venta.get(86590).serialize(), cls=ModelEncoder)
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    app.merge(bodega_api_app)
    app.merge(w)
    run(app, host=host, debug=True, port=8080)
    return 'http://localhost:8080'


if __name__ == '__main__':
    old = InvApiOld(sessionfactory())
    start_date = datetime.date(2013,02,20)
    end_date = datetime.date(2013,03,20)
    for x in old.get_dated_report(start_date, end_date, 1):
        print x.codigo, x.total
    main()



