import json
import os
import shutil
import unittest

import bottle
from webtest import TestApp
from henry.background_sync import sync_api
from henry.base.fileservice import FileService

class SyncTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        bottle.debug(True)
        prefix = '/app'
        tmpdir = '/tmp/test'
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)
        os.mkdir(tmpdir)
        fileservice = FileService(tmpdir)
        sync_api.FINAL_LOG_DIR = tmpdir
        cls.test_app = TestApp(sync_api.make_wsgi_api(prefix, fileservice))

    def tearDown(self):
        pass

    def test_sync(self):
        content = {
            'meta': {
                'almacen_id': 1,
                'date': '2011-01-01',
                'batch': 1,
            },
            'action_type': 'new_prod',
            'content': {
                'some': {
                    'nested': ['content']
                }
            }
        }
        data = '\n'.join([json.dumps(content), json.dumps(content)])

        self.test_app.post('/app/logs', params=data)
        
        paths = os.listdir(sync_api.FINAL_LOG_DIR + '/1')
        self.assertEquals(1, len(paths))

        with open(os.path.join(sync_api.FINAL_LOG_DIR + '/1', paths[0])) as f:
            for line in f.readlines():
                content2 = json.loads(line)
                self.assertEquals(content, content2)


if __name__ == '__main__':
    unittest.main()
