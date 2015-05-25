import os

class FileService:

    def __init__(self, root):
        self.root = root

    def put_file(self, filename, content, override=True):
        dirname, name = os.path.split(filename)
        if not filename.startswith('/'):
            dirname = os.path.join(self.root, dirname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        fullpath = os.path.join(dirname, name)
        with open(fullpath, 'w') as f:
            f.write(content)
            f.flush()

    def get_file(self, filename):
        if not filename.startswith('/'):
            filename = os.path.join(self.root, filename)
        if not os.path.exists(filename):
            return None
        with open(name) as f:
            return f.read()

