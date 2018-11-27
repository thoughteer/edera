from edera.helpers.boxes import SimpleBox


class Bean(SimpleBox):

    def __new__(cls):
        return SimpleBox()
