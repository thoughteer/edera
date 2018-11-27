from edera.managers import MongoManager


def test_manager_destroys_client_on_exit(mongo):
    with MongoManager(mongo):
        instance = mongo.instance
        assert mongo.instance is instance
    assert mongo.instance is not instance
