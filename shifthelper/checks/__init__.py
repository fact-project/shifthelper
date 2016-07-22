# -*- coding:utf-8 -*-
from __future__ import print_function
from threading import Thread
from threading import Event
from traceback import format_exc
import logging
import os

from collections import namedtuple

class Message:
    pass


class SystemStatusMessage(Message):
    def __init__(self, name, value, unit):
        self.name = name
        self.value = value
        self.unit = unit
    def __repr__(self):
        return self.__class__.__name__ + '(%r)' % self.__dict__


class FlareMessage(Message):
    def __init__(self, source, rate, image):
        self.source = source
        self.rate = rate
        self.image = image
    def __repr__(self):
        d = self.__dict__
        del d["image"]
        return self.__class__.__name__ + '(%r)' % d



from queue import Queue
class Check(Thread):
    instances = []
    stop_event = Event()
    messages = Queue()
    '''
    Subclasses need to implement the check method.
    This method has to push a string (unicode) message into
    the queue if something goes wrong.

    All Exceptions in this Thread are catched and their messages
    are also pushed into the queue.

    The thread has to be started with the .start() method, it
    will terminate if stop_event.set() is called.

    In your main thread, this requires that KeyboardInterrupt and SystemExit
    are catched to first call stop_event.set() and then terminate the
    program.
    '''
    def __init__(self, interval):
        self.queue = Check.messages
        self.interval = interval
        self.logger = logging.getLogger(__name__)
        Check.instances.append(self)
        super().__init__()

    def run(self):
        while not Check.stop_event.is_set():
            try:
                self.check()
            except Exception as e:
                self.queue.put(format_exc())
                self.logger.exception(e)
            Check.stop_event.wait(self.interval)

    def check(self):
        raise NotImplementedError

from . import webdim
from . import qla
