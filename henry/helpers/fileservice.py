import os

class FileService:

    def __init__(self, root):
        self.root = root


    def put_file(self, filename, content, override=True):
        dirname, name = os.path.split(filename)
        dirname = os.path.join(self.root, dirname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        fullpath = os.path.join(dirname, name)
        with open(fullpath, 'w') as f:
            f.write(content)
            f.flush()

    def get_file(self, filename):
        name = os.path.join(self.root, filename)
        if not os.path.exists(name):
            return None
        with open(name) as f:
            return f.read()
