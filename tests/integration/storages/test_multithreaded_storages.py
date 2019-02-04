from edera.invokers import MultiThreadedInvoker


def test_storage_is_multithreaded(multithreaded_storage):

    def put(index):
        multithreaded_storage.put(str(index), str(index**2))

    MultiThreadedInvoker({str(i): lambda i=i: put(i) for i in range(5)}).invoke()
    for index in range(5):
        assert len(multithreaded_storage.get(str(index))) == 1
