# -*- coding:utf-8 -*-
from __future__ import print_function
from threading import Thread
from blessings import Terminal
from datetime import datetime
from subprocess import check_output

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
        for i, (key, val) in enumerate(self.status_data.iteritems()):
            print(self.term.move(3+i, 0) + u'{:<20}  {:>6} {:<6}'.format(
                key, *val
            ))

        print(self.term.move(2, 40) + 'Maximum Source Activity')
        for i, (key, val) in enumerate(self.qla_data.iteritems()):
            print(self.term.move(3+i, 40) + u'{:<20}  {:>6} {:<6}'.format(
                key, *val
            ))

        if self.logfile is not None:
            logs = check_output('tail -n10 {}'.format(self.logfile), shell=True)
            print(self.term.move(15, 0) + logs)

        print(self.term.move(25, 0))


def enter_phone_number():
    my_phone_number = raw_input(
        'Please enter your phone number (like +4912345)\n'
    )
    my_phone_number = my_phone_number.replace(' ', '')
    return my_phone_number


def confirm_phone_number(caller):
    print("You entered: ", caller.phone_number)
    if not ask_user('Is that number correct?'):
        caller.phone_number = None


def try_to_call(caller):
    """ Returns if the call worked or not.
    """
    print("I will try to call you now")
    caller.place_call()

    if ask_user('Did your phone ring?'):
        caller.hangup()
        return True
    return False


def check_phone_number(caller):
    calling_worked = False
    while (not calling_worked or caller.phone_number is None):
        if caller.phone_number is None:
            caller.phone_number = enter_phone_number()
        confirm_phone_number(caller)

        if caller.phone_number is not None:
            calling_worked = try_to_call(caller)


def ask_user(question):
    answer = raw_input(question + ' (y/n): ')
    if answer.lower().startswith('y'):
        return True
    else:
        return False
