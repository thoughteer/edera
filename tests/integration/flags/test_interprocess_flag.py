import multiprocessing


def test_flag_can_be_raised_from_another_process(interprocess_flag):

    def raise_it():
        interprocess_flag.up()

    raiser = multiprocessing.Process(target=raise_it)
    raiser.daemon = True
    raiser.start()
    raiser.join()
    assert interprocess_flag.raised


def test_flag_can_be_lowered_from_another_process(interprocess_flag):

    def raise_it():
        interprocess_flag.down()

    interprocess_flag.up()
    raiser = multiprocessing.Process(target=raise_it)
    raiser.daemon = True
    raiser.start()
    raiser.join()
    assert not interprocess_flag.raised
