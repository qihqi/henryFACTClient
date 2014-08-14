import bottle

w = bottle.Bottle()

@w.get('/app/crear_ingreso')
def create_increase():
    return bottle.static_file('static/ingreso.html', root='.')

@w.post('/app/crear_ingreso')
def post_create_increse():
    pass

