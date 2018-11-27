from edera.helpers.beanbag import split
from tests.unit.helpers.beans import my_splitter


@split(my_splitter.get)
class Bean(object):

    def __init__(self):
        self.value = my_splitter.get()

    def square(self):
        return self.value**2
