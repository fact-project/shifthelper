#!/usr/bin/env ipython
# coding: utf-8
from __future__ import print_function
import time
from datetime import datetime
from blessings import Terminal
term = Terminal()
import handle_QLA
import handle_dim_stuff
import handle_cmd_line_UI
import handle_Skype

handle_dim_stuff.setup()
handle_QLA.setup()

my_phone_number = handle_cmd_line_UI.get_tested_phone_number()

delay_between_checks = 60  # in sec.
assert handle_Skype.phone_ringing_time < delay_between_checks
while True:
    try:
        # the perform_checks() functions throw an Exception
        # if the shifter needs to be called
        print('\n'+term.cyan(datetime.utcnow()))
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
