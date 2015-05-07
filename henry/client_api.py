import json
from bottle import Bottle, request, abort
from henry.config import clientapi, dbcontext
from henry.layer2.client import Client


client_api_app = Bottle()
w = client_api_app


@w.get('/api/cliente/<codigo>')
@dbcontext
def get_cliente(codigo):
    client = clientapi.get(codigo)
    if client is None:
        abort(404, 'cliente no encontrado')
    return client.to_json()


@w.put('/api/cliente/<codigo>')
@dbcontext
def update_client(codigo):
    client_dict = json.parse(request.body)
    client = Client.deserialize(client_dict)
    clientapi.save(client)
    return {'codigo': client.codigo}


@w.post('/api/cliente/<codigo>')
def create_client(codigo):
    return update_client(codigo)

