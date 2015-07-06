#!/usr/bin/env ipython
# coding: utf-8
from __future__ import print_function
import time
import handle_QLA
import handle_dim_stuff
import handle_cmd_line_UI
from handle_Skype import skype

handle_dim_stuff.setup()
handle_QLA.setup()
my_phone_number = handle_cmd_line_UI.get_tested_phone_number()
while True:
    try:
        # the perform_checks() functions throw an Exception
        # if the shifter needs to be called
        handle_dim_stuff.perform_checks()
        handle_QLA.perform_checks()
        print(term.green("Everything OK!"))
        time.sleep(delay_between_checks)
    except KeyboardInterrupt, SystemExit:
        raise
    except Exception as e:
        print(e)
        handle_Skype.call(my_phone_number)
        time.sleep(delay_between_checks)
