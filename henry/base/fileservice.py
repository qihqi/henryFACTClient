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
        if not filename.startswith('/'):
            filename = os.path.join(self.root, filename)
        if not os.path.exists(filename):
            return None
        with open(filename) as f:
            return f.read()

    def append_file(self, filename, data):
        fullpath = self.make_fullpath(filename)
        with open(fullpath, 'a') as f:
            with LockClass(f):
                f.write(data)
                f.write('\n')
                f.flush()
        return fullpath

    def get_file_lines(self, filenames, condition):
        #        result = []
        #        def worker(filename, dest):
        #            with open(filename) as f:
        #                for line in f.readlines():
        #                    if condition(line):
        #                        dest.append(line)
        threads = []
        for fname in filenames:
            fullpath = self.make_fullpath(fname)
            if os.path.exists(fullpath):
                # t = threading.Thread(target=worker, args=(fullpath, result))
                # threads.append(t)
                # t.start()
                with open(fullpath) as f:
                    for line in f.readlines():
                        if condition(line):
                            yield line

                            # map(threading.Thread.join, threads)
                            # return result


class LockClass:
    def __init__(self, fileobj):
        self.fileno = fileobj.fileno()

    def __enter__(self):
        fcntl.flock(self.fileno, fcntl.LOCK_EX)

    def __exit__(self, _, unused, enused2):
        fcntl.flock(self.fileno, fcntl.LOCK_UN)
