# -*- coding:utf-8 -*-
from __future__ import absolute_import, print_function, division
from ..cli import enter_phone_number, ask_user


class Caller(object):
    def __init__(self, phone_number, ring_time):
        self.ring_time = ring_time
        self.phone_number = phone_number

    def hangup(self):
        raise NotImplementedError

    def place_call(self):
        raise NotImplementedError

    def check_phone_number(self):
        calling_worked = False
        while (not calling_worked or self.phone_number is None):
            if self.phone_number is None:
                self.phone_number = enter_phone_number()
            self.confirm_phone_number()

            if self.phone_number is not None:
                print('I will try to call you now')
                self.place_call()

                if ask_user('Did your phone ring?'):
                    self.hangup()
                    calling_worked = True

    def confirm_phone_number(self):
        print('You entered: ', self.phone_number)
        if not ask_user('Is that number correct?'):
            self.phone_number = None


class NoCaller(Caller):
    """ Dummy caller for debugging only """
    def __init__(self, *args, **kwargs):
        self.phone_number = "nothing"
        pass

    def hangup(self):
        pass

    def place_call(self):
        pass

    def check_phone_number(self):
        pass

    def confirm_phone_number(self):
        pass
