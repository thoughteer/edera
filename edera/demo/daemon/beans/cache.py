import os.path

from edera.demo.daemon.beans import arguments
from edera.storages import SQLiteStorage


class Bean(SQLiteStorage):

    def __new__(cls):
        return SQLiteStorage(os.path.join(arguments.root, "cache.db"))
