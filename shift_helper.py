#!/usr/bin/env ipython
# coding: utf-8
from __future__ import print_function
import time
import sys
from datetime import datetime
from blessings import Terminal
term = Terminal()
import handle_QLA
import handle_dim_stuff
import handle_cmd_line_UI
import handle_Skype
from fact_exceptions import FACTException

handle_dim_stuff.setup()
handle_QLA.setup()

my_phone_number = handle_cmd_line_UI.get_tested_phone_number()

delay_between_checks = 60  # in sec.
assert handle_Skype.phone_ringing_time < delay_between_checks
while True:
    try:
        # the perform_checks() functions throw an FACTException
        # if the shifter needs to be called
        print('\n'+term.cyan(datetime.utcnow()))
        handle_dim_stuff.perform_checks()
        handle_QLA.perform_checks()
        print(term.green("Everything OK!"))
        time.sleep(delay_between_checks)
    except (KeyboardInterrupt, SystemExit):
        sys.exit(0)
    except FACTException as e:
        print(type(e), ":\n", e)
        handle_Skype.call(my_phone_number)
        time.sleep(delay_between_checks)
    except Exception as e:
        print(e)
        handle_Skype.call(my_phone_number)
        time.sleep(delay_between_checks)
