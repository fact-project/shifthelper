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
        'Please enter your phone number (like +4912345) or skype name\n'
    )
    my_phone_number = my_phone_number.replace(' ', '')
    return my_phone_number


def confirm_phonenumber(caller):
    print("You entered: ", caller.phonenumber)
    confirm_correctness = raw_input('Is that number correct? (y/n): ')
    if not confirm_correctness.lower().startswith('y'):
        caller.phonenumber = None


def try_to_call(caller):
    """ Returns if the call worked or not.
    """
    print("I will try to call you now")
    caller.place_call()
    recieved_call = raw_input('Did your phone ring? (y/n): ')
    if recieved_call.lower().startswith('y'):
        caller.hangup()
        return True
    return False


def check_phonenumber(caller):
    calling_worked = False
    while (not calling_worked or caller.phonenumber is None):
        if caller.phonenumber is None:
            caller.phonenumber = enter_phone_number()
        confirm_phonenumber(caller)

        if caller.phonenumber is not None:
            calling_worked = try_to_call(caller)


def ask_telegram():
    answer = raw_input(
        'Do you want to use the telegram messenger to get error messages? (y/n)'
    )
    if answer.lower().startswith('y'):
        return True
    else:
        return False