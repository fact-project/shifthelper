# -*- coding:utf-8 -*-
from __future__ import print_function
from threading import Thread
from traceback import format_exc
import logging
import os

class Check(Thread):
    instances = []
    '''
    base class for the checks
    this class is the base implementation for the checks

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
    def __init__(self, queue, interval, stop_event,
                 qla_data, system_status):
        self.queue = queue
        self.interval = interval
        self.stop_event = stop_event
        self.logger = logging.getLogger('shift_helper.Check')

        assert isinstance(qla_data, dict), 'qla_data has to be a dict'
        self._qla_data = qla_data
        assert isinstance(system_status, dict), 'system_status has to be a dict'
        self._system_status = system_status
        Check.instances.append(self)
        super().__init__()


    def run(self):
        while not self.stop_event.is_set():
            try:
                self.check()
            except Exception as e:
                self.queue.append(format_exc())
                self.logger.exception(e)
            self.stop_event.wait(self.interval)

    def check(self):
        raise NotImplementedError

    def update_system_status(self, name, value, unit):
        '''
        Updates the system_status dict which is used by the
        command line status display.

        e.g. name='wind speed', value=10, unit='km/h'
        '''
        self._system_status[name] = (value, unit)

    def update_qla_data(self, source, rate):
        '''
        Updates the system_status dict which is used by the
        command line status display.

        e.g. name='wind speed', value=10, unit='km/h'
        '''
        self._qla_data[source] = (rate, '1/h')


