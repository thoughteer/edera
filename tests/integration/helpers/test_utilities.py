import datetime

import edera.helpers


def test_sleep_works_correctly():

    def tick():
        counter[0] += 1

    counter = [0]
    start_time = datetime.datetime.utcnow()
    edera.helpers.sleep[tick](datetime.timedelta(seconds=3))
    assert counter[0] >= 2
    assert datetime.datetime.utcnow() - start_time < datetime.timedelta(seconds=5)
