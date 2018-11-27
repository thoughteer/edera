from edera.demo.daemon.beans import colorful
from edera.demo.daemon.beans import settings
from edera.demo.fs import FileSystem


@colorful
class Bean(FileSystem):

    def __new__(cls):
        return FileSystem(settings.root)
