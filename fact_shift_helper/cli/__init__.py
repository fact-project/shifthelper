# -*- coding:utf-8 -*-
from __future__ import print_function
from threading import Thread
from blessings import Terminal
from datetime import datetime
from subprocess import check_output
from six.moves import input
import six

term = Terminal()


def timestamp():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')


class StatusDisplay(Thread):

    def __init__(self, qla_data, status_data, stop_event, logfile=None):
        self.status_data = status_data
        self.qla_data = qla_data
        self.term = Terminal()
        self.stop_event = stop_event
        self.logfile = logfile
        super(StatusDisplay, self).__init__()

    def run(self):
        with self.term.fullscreen(), self.term.hidden_cursor():
            print(self.term.clear())
            while not self.stop_event.is_set():
                self.update_status()
                self.stop_event.wait(5)

    def update_status(self):
        print(self.term.clear())
        print(self.term.move(0, 0) + self.term.cyan(timestamp()))

        print(self.term.move(2, 0) + 'System Status')
        for i, (key, val) in enumerate(six.iteritems(self.status_data)):
            print(self.term.move(3+i, 0) + u'{:<20}  {:>6} {:<6}'.format(
                key, *val
            ))

        print(self.term.move(2, 40) + 'Maximum Source Activity')
        for i, (key, val) in enumerate(six.iteritems(self.qla_data)):
            print(self.term.move(3+i, 40) + u'{:<20}  {:>6} {:<6}'.format(
                key, *val
            ))

        if self.logfile is not None:
            logs = check_output('tail -n20 {}'.format(self.logfile), shell=True)
            n_lines = term.height - 15
            loglines = list(
                reversed(logs.decode('utf-8').splitlines())
            )[:n_lines]
            print(self.term.move(14, 0) + '\n'.join(loglines))


def enter_phone_number():
    my_phone_number = input(
        'Please enter your phone number (like +4912345)\n> '
    )
    my_phone_number = my_phone_number.replace(' ', '')
    return my_phone_number


def ask_user(question):
    answer = input(question + ' (y/n): ')
    if answer.lower().startswith('y'):
        return True
    else:
        return False
