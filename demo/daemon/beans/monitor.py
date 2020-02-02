import os.path

from edera.storages import SQLiteStorage

from . import arguments


class Bean(SQLiteStorage):

    def __new__(cls):
        return SQLiteStorage(os.path.join(arguments.root, "monitor.db"))
