from __future__ import print_function
import handle_Skype
import time
from Skype4Py import SkypeError


def enter_phone_number():
    my_phone_number = raw_input(
        'Please enter your phone number like +1234\n')
    my_phone_number = my_phone_number.replace(' ', '')
    return my_phone_number


def confirm_phonenumber(my_phone_number):
    print("You entered: ", my_phone_number)
    confirm_correctness = raw_input('Is that number correct? (y/n): ')
    if not confirm_correctness.lower()[0] == 'y':
        my_phone_number = None
    return my_phone_number


def try_to_call(my_phone_number):
    """ Returns if the call worked or not.
    """
    print("I will try to call you now")
    handle_Skype.call(my_phone_number)
    recieved_call = raw_input('Did your phone ring? (y/n): ')
    if recieved_call.lower()[0] == 'y':
        return True
    return False


def check_phonenumber(my_phone_number):
    calling_worked = False
    while (not calling_worked or my_phone_number is None):
        if my_phone_number is None:
            my_phone_number = enter_phone_number()
        my_phone_number = confirm_phonenumber(my_phone_number)

        if my_phone_number is not None:
            calling_worked = try_to_call(my_phone_number)

    return my_phone_number
