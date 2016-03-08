# -*- coding:utf-8 -*-
from __future__ import print_function
from threading import Thread
from datetime import datetime
from subprocess import check_output
from six.moves import input
import six


def timestamp():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')


class StatusDisplay(Thread):

    def __init__(self, qla_data, status_data, stop_event, logfile=None):
        self.status_data = status_data
        self.qla_data = qla_data
        self.stop_event = stop_event
        self.logfile = logfile
        super(StatusDisplay, self).__init__()

    def run(self):        
        while not self.stop_event.is_set():
            self.update_status()
            self.stop_event.wait(5)

    def update_status(self):
        print(timestamp())

        print('System Status')
        for i, (key, val) in enumerate(six.iteritems(self.status_data)):
            print(u'{:<20}  {:>6} {:<6}'.format(key, *val))

        print('Maximum Source Activity')
        for i, (key, val) in enumerate(six.iteritems(self.qla_data)):
            print(u'{:<20}  {:>6} {:<6}'.format(key, *val))

        if self.logfile is not None:
            loglines = open(self.logfile, 'r').readlines()[-10::-1]
            print(''.join(loglines))


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
