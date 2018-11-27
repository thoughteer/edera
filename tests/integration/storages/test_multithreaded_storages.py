from edera.invokers import MultiThreadedInvoker


def test_storage_is_multithreaded(multithreaded_storage):

    def put(index):
        multithreaded_storage.put(str(index), str(index**2))

    MultiThreadedInvoker({str(i): lambda i=i: put(i) for i in range(5)}).invoke()
    assert {(key, value) for key, _, value in multithreaded_storage.gather()} == {
        ("0", "0"),
        ("1", "1"),
        ("2", "4"),
        ("3", "9"),
        ("4", "16"),
    }
