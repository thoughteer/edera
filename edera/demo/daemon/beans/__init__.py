import os
import threading

from edera.helpers import Beanbag
from edera.helpers.beanbag import split


def colorful(bean_class):
    from edera.demo.daemon.beans import colorbox
    return split(lambda: colorbox.get())(threadsafe(bean_class))


def threadsafe(bean_class):
    return split(os.getpid, threading.current_thread)(bean_class)


Beanbag(__name__)
