# -*- coding:utf-8 -*-
from __future__ import print_function
from blessings import Terminal

term = Terminal()


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
