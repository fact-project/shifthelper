# -*- coding:utf-8 -*-
from __future__ import print_function
from threading import Thread
from datetime import datetime
from blessings import Terminal
from traceback import format_exc
term = Terminal()

class Check(Thread):
    def __init__(self, queue, interval, stop_event,
                 qla_data=None, system_status=None):
        self.queue = queue
        self.interval = interval
        self.stop_event = stop_event
        self.qla_data = qla_data
        self.system_status = system_status
        super(Check, self).__init__()

    def run(self):
        while not self.stop_event.is_set():
            try:
                self.check()
                self.stop_event.wait(self.interval)
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                self.queue.append(format_exc())

    def check(self):
        raise NotImplementedError


class Alert(Thread):
    def __init__(self, queue, interval, stop_event, caller=None, messenger=None):
        self.queue = queue
        self.interval = interval
        self.stop_event = stop_event
        self.caller = caller
        self.messenger = messenger
        self.errors = 0

        super(Alert, self).__init__()

    def run(self):
        while not self.stop_event.is_set():
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S -- ')
            if len(self.queue) > 0:
                if self.caller is not None:
                    self.caller.place_call()
                while len(self.queue) > 0:
                    message = self.queue.popleft()
                    self.errors += 1
                    if self.messenger is not None:
                        self.messenger.send_message(message)
                    print(term.move(self.errors+10, 0) + term.red(now + message))

            self.stop_event.wait(self.interval)
