import time

import pymongo
import pymongo.errors

from edera.exceptions import StorageOperationError
from edera.storage import Storage


class MongoStorage(Storage):
    """
    A MongoDB-based storage.

    It uses a MongoDB collection to store versioned key-value pairs.

    This implementation is both thread-safe and fork-safe as long as you use the lazy MongoDB
    client correctly.
    Please, consider using $MongoManager to start/stop client connections.

    Attributes:
        mongo (Lazy[pymongo.MongoClient]) - the lazy MongoDB client
        database (pymongo.database.Database) - the MongoDB database used
        collection (pymongo.collection.Collection) - the MongoDB collection used

    See also:
        $MongoManager
    """

    def __init__(self, mongo, database, collection):
        """
        Args:
            mongo (Lazy[pymongo.MongoClient]) - a lazy MongoDB client
            database (String) - the name of a MongoDB database to use
            collection (String) - the name of a MongoDB collection to use
        """
        self.mongo = mongo
        self.__database = database
        self.__collection = collection

    def clear(self):
        try:
            self.collection.delete_many({})
        except pymongo.errors.PyMongoError as error:
            raise StorageOperationError("failed to write to the MongoDB collection: %s" % error)

    @property
    def collection(self):
        result = self.database[self.__collection]
        try:
            result.create_index([("key", pymongo.ASCENDING), ("version", pymongo.ASCENDING)])
        except pymongo.errors.PyMongoError as error:
            raise StorageOperationError("failed to create index: %s" % error)
        return result

    @property
    def database(self):
        return self.mongo.instance[self.__database]

    def delete(self, key, till=None):
        selector = {"key": key}
        if till is not None:
            selector.update({"version": {"$lt": till}})
        try:
            self.collection.delete_many(selector)
        except pymongo.errors.PyMongoError as error:
            raise StorageOperationError("failed to write to the MongoDB collection: %s" % error)

    def gather(self):
        try:
            documents = list(self.collection.find({}))
        except pymongo.errors.PyMongoError as error:
            raise StorageOperationError("failed to read from the MongoDB collection: %s" % error)
        return [self.__decode_document(document) for document in documents]

    def get(self, key, since=None, limit=None):
        if limit == 0:  # pymongo is weird and treats 0 as "no limit"
            return []
        selector = {"key": key}
        if since is not None:
            selector.update({"version": {"$gte": since}})
        try:
            documents = self.collection.find(selector).sort("version", pymongo.DESCENDING)
            if limit is not None:
                documents = documents.limit(limit)
            documents = list(documents)
        except pymongo.errors.PyMongoError as error:
            raise StorageOperationError("failed to read from the MongoDB collection: %s" % error)
        return [(version, value) for _, version, value in map(self.__decode_document, documents)]

    def put(self, key, value):
        try:
            version = int(time.time() * 10**9)
            self.collection.insert_one({"key": key, "version": version, "value": value})
            return version
        except pymongo.errors.PyMongoError as error:
            raise StorageOperationError("failed to read from the MongoDB collection: %s" % error)

    def __decode_document(self, document):
        return (document["key"], document["version"], document["value"])
