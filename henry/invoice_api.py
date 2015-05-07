import json
from bottle import Bottle, request, abort
from henry.config import dbcontext, invapi, clientapi, auth_decorator
from henry.layer2.invoice import InvMetadata
from henry.layer2.documents import DocumentCreationRequest
from henry.helpers.serialization import json_dump

w = invoice_api_app = Bottle()


@w.get('/api/nota/<inv_id>')
@dbcontext
@auth_decorator
def get_invoice(inv_id):
    doc = invapi.get_doc(inv_id)
    if doc is None:
        abort(404, 'Nota no encontrado')
        return
    return json_dump(doc.serialize())


@w.post('/api/nota')
@dbcontext
@auth_decorator
def create_invoice():
    json_content = request.body.read()
    content = json.loads(json_content)

    meta = InvMetadata.deserialize(content['meta'])
    doc_request = DocumentCreationRequest(meta)
    for prod_id, cant in doc_request.items:
        cant = int(cant)
        if cant > 0:
            doc_request.add(prod_id, cant)

    client_id = content['meta']['client_id']
    client = clientapi.get(client_id)
    doc_request.meta.client = client
    doc = invapi.create_document_from_request(doc_request)
    invoice = invapi.save(doc)
    return {'codigo': invoice.meta.uid}


@w.put('/api/nota/<uid>')
@dbcontext
@auth_decorator
def postear_invoice(uid):
    t = invapi.commit(uid=uid)
    return {'status': t.meta.status}


@w.delete('/api/nota/<uid>')
@dbcontext
@auth_decorator
def delete_invoice(uid):
    t = invapi.delete(uid=uid)
    return {'status': t.meta.status}
