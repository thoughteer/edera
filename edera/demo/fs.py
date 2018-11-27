import contextlib
import os
import os.path
import shutil
import tempfile


class FileSystem(object):

    def __init__(self, root):
        self.root = root

    def check(self, path):
        return os.path.exists(os.path.join(self.root, path))

    @contextlib.contextmanager
    def create(self, path):
        path = os.path.join(self.root, path)
        tdescriptor, tpath = None, None
        try:
            tdescriptor, tpath = tempfile.mkstemp()
            with open(tpath, "w") as stream:
                yield stream
            os.rename(tpath, path)
        finally:
            if tdescriptor is not None:
                os.close(tdescriptor)
                if os.path.exists(tpath):
                    os.remove(tpath)

    def ensure(self, path):
        return os.makedirs(os.path.join(self.root, path))

    def read(self, path):
        return open(os.path.join(self.root, path), "r")

    def remove(self, path):
        path = os.path.join(self.root, path)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
