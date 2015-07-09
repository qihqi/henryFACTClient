import os
import fcntl
# import threading


class FileService:
    def __init__(self, root):
        self.root = root

    def make_fullpath(self, filename):
        dirname, name = os.path.split(filename)
        if not filename.startswith('/'):
            dirname = os.path.join(self.root, dirname)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        fullpath = os.path.join(dirname, name)
        return fullpath

    def put_file(self, filename, content, override=True):
        fullpath = self.make_fullpath(filename)
        if not override and os.path.exists(fullpath):
            return None
        with open(fullpath, 'w') as f:
            f.write(content)
            f.flush()
            return fullpath

    def get_file(self, filename):
        fullpath = self.make_fullpath(filename)
        if not os.path.exists(fullpath):
            return None
        with open(fullpath) as f:
            return f.read()

    def append_file(self, filename, data):
        fullpath = self.make_fullpath(filename)
        with open(fullpath, 'a') as f:
            with LockClass(f):
                f.write(data)
                f.write('\n')
                f.flush()
        return fullpath

    def get_file_lines(self, filenames, condition=None):
        if condition is None:
            condition = lambda x: True
        for fname in filenames:
            fullpath = self.make_fullpath(fname)
            if os.path.exists(fullpath):
                with open(fullpath) as f:
                    for line in f.readlines():
                        if condition(line):
                            yield line


class LockClass:
    def __init__(self, fileobj):
        self.fileno = fileobj.fileno()

    def __enter__(self):
        fcntl.flock(self.fileno, fcntl.LOCK_EX)

    def __exit__(self, _, unused, enused2):
        fcntl.flock(self.fileno, fcntl.LOCK_UN)
