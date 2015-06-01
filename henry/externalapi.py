import os
from urlparse import urljoin
import requests
from henry.helpers.serialization import json_dump

class ExternalApi:

    def __init__(self, root, path, user=None, password=None):
        self.root = root
        self.path = path
        self.user = user
        self.password = password
        self.cookies = None

    def authenticate(self):
        auth_url = urljoin(self.root, '/authenticate')
        r = requests.post(auth_url, data={'username': self.user, 'password': self.password})
        self.cookies = r.cookies

    def execute_query_with_auth(self, func, url, data=None):
        response = func(url, data=data, allow_redirects=False, cookies=self.cookies)
        if response.status_code / 100 == 3:
            self.authenticate()
            response = func(url, data=data, allow_redirects=False, cookies=self.cookies)
        return response

    def save(self, doc):
        url = os.path.join(self.root, self.path)
        del doc.meta.timestamp
        response = self.execute_query_with_auth(requests.post, url, json_dump(doc.serialize()))
        if response.status_code != 200:
            return None
        codigo = response.json()['codigo']
        doc.meta.uid = codigo
        return doc

    def commit(self, doc):
        url = os.path.join(self.root, self.path, doc.meta.uid)
        if self.execute_query_with_auth(requests.put, url):
            return doc
        return None

    def delete(self, doc):
        url = os.path.join(self.root, self.path, doc.meta.uid)
        if self.execute_query_with_auth(requests.delete, url):
            return doc
        return None
