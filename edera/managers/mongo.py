class MongoManager(object):
    """
    A context manager that stops/closes a given lazy $pymongo.MongoClient instance on exit.

    Attributes:
        mongo (Lazy[pymongo.MongoClient]) - the managed lazy MongoDB client
    """

    def __enter__(self):
        pass

    def __exit__(self, *args):
        try:
            self.mongo.instance.close()
        finally:
            self.mongo.destroy()

    def __init__(self, mongo):
        """
        Args:
            mongo (Lazy[pymongo.MongoClient]) - a lazy MongoDB client
        """
        self.mongo = mongo

    def __repr__(self):
        return "<%s: mongo-id %x>" % (self.__class__.__name__, id(self.mongo))
