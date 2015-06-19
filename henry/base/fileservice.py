import os
import fcntl

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
        if not override and os.path.exists(fullpath):
            return None
        with open(fullpath, 'w') as f:
            f.write(content)
            f.flush()
            return fullpath

    def get_file(self, filename):
        if not filename.startswith('/'):
            filename = os.path.join(self.root, filename)
        if not os.path.exists(filename):
            return None
        with open(filename) as f:
            return f.read()


class LockClass:

    def __init__(self, fileobj):
        self.fileno = fileobj.fileno()

    def __enter__(self):
        fcntl.flock(self.fileno, fcntl.LOCK_EX)

    def __exit__(self, _, unused, enused2):
        fcntl.flock(self.fileno, fcntl.LOCK_UN)
