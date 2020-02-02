from . import colorful
from . import settings
from ...fs import FileSystem


@colorful
class Bean(FileSystem):

    def __new__(cls):
        return FileSystem(settings.root)
