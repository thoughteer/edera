def test_beanbag_imports_beans_correctly():
    from .beans import my_bean
    assert my_bean.square(5) == 28
    assert my_bean[5] == 28


def test_bean_splitting_works_correctly():
    from .beans import my_split_bean
    from .beans import my_splitter
    my_splitter.put(2)
    assert my_split_bean.square() == 4
    my_splitter.put(3)
    assert my_split_bean.square() == 9
