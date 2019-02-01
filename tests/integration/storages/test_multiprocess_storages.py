from edera.invokers import MultiProcessInvoker


def test_storage_is_multiprocess(multiprocess_storage):

    def put(index):
        multiprocess_storage.put(str(index), str(index**2))

    MultiProcessInvoker({str(i): lambda i=i: put(i) for i in range(5)}).invoke()
    for index in range(5):
        assert len(multiprocess_storage.get(str(index))) == 1
