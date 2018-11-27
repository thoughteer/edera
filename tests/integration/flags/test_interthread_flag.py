import threading


def test_flag_can_be_raised_from_another_thread(interthread_flag):

    def raise_it():
        interthread_flag.up()

    raiser = threading.Thread(target=raise_it)
    raiser.daemon = True
    raiser.start()
    raiser.join()
    assert interthread_flag.raised


def test_flag_can_be_lowered_from_another_thread(interthread_flag):

    def raise_it():
        interthread_flag.down()

    interthread_flag.up()
    raiser = threading.Thread(target=raise_it)
    raiser.daemon = True
    raiser.start()
    raiser.join()
    assert not interthread_flag.raised
