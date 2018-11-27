from tests.unit.helpers.beans import my_other_bean


class Bean(object):

    def __getitem__(self, key):
        return self.square(key)

    def square(self, value):
        return value**2 + my_other_bean
