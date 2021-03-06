import os
import threading

from edera.helpers import Beanbag
from edera.helpers.beanbag import split


def colorful(bean_class):
    from . import colorbox
    return split(lambda: colorbox.get())(threadsafe(bean_class))


def threadsafe(bean_class):
    return split(os.getpid, lambda: threading.current_thread().ident)(bean_class)


Beanbag(__name__)
