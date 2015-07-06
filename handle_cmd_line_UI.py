import sys
import handle_Skype

# examples:
#     my_phone_number = '+123456789'   # calls you on your phone
#     my_phone_number = None           # if you want to be asked for it on the command line
#     my_phone_number = 'dominikneise' # calls you on your skype account

my_phone_number = None


def enter_phone_number():
    my_phone_number = raw_input(
        'Please enter your phone number like +1234\n')
    my_phone_number = my_phone_number.replace(' ', '')


def confirm_phonenumber():
    global my_phone_number
    print("You entered: ", my_phone_number)
    confirm_correctness = raw_input('Is that number correct? (y/n): ')
    if not confirm_correctness.lower()[0] == 'y':
        my_phone_number = None


def try_to_call():
    """ Returns if the call worked or not.
    """
    print("I will try to call you now")
    try:
        handle_Skype.call(my_phone_number)
        recieved_call = raw_input('Did your phone ring? (y/n): ')
        if recieved_call.lower()[0] == 'y':
            return True
    except Skype4Py.SkypeError:
        print("Could not call you, I'll try again in 10s")
        time.sleep(10)
        return False


def get_tested_phone_number():
    global my_phone_number
    if len(sys.argv) > 1:
        my_phone_number = sys.argv[1]
    else:
        my_phone_number = None

    calling_worked = False
    while (not calling_worked or my_phone_number is None):
        if my_phone_number is None:
            enter_phone_number()
        confirm_phonenumber()

        if my_phone_number is not None:
            calling_worked = try_to_call()

    return my_phone_number
