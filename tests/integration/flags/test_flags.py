def test_flag_is_initially_lowered(flag):
    assert not flag.raised


def test_unshared_flag_works_correctly(flag):
    flag.up()
    assert flag.raised
    flag.down()
    assert not flag.raised
    flag.up()
    assert flag.raised
