from edera.invokers import MultiProcessInvoker


def test_storage_is_multiprocess(multiprocess_storage):

    def put(index):
        multiprocess_storage.put(str(index), str(index**2))

    MultiProcessInvoker({str(i): lambda i=i: put(i) for i in range(5)}).invoke()
    assert {(key, value) for key, _, value in multiprocess_storage.gather()} == {
        ("0", "0"),
        ("1", "1"),
        ("2", "4"),
        ("3", "9"),
        ("4", "16"),
    }
