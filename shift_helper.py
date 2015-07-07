#!/usr/bin/env ipython
# coding: utf-8
'''
This script is intended to call the shifter
of security or flare alert limits are reached.
Please do not accept or deny the call as this will
create costs for us. Just let it ring.
<phonenumber> can either be a real phonenumber or a skype account.

Usage:
    shift_helper.py [<phonenumber>] [options]

Options
    --debug  start the program in debug mode, DO NOT USE ON SHIFT
             this will not start a call if a programming error occures
             and will not check the the dimctrl status for a running Main.js

    --interval=<N>  the interval between the cecks in seconds [default: 60]

    --ringtime=<N>  how long skype wil lett you phone ring [default: 15]
'''
from __future__ import print_function
import time
from datetime import datetime
from blessings import Terminal
import handle_QLA
import handle_dim_stuff
import handle_cli
import handle_Skype
from fact_exceptions import FACTException
from docopt import docopt
import sys


def main():
    term = Terminal()
    args = docopt(__doc__)

    args['--interval'] = float(args['--interval'])
    args['--ringtime'] = float(args['--ringtime'])
    assert args['--ringtime'] < args['--interval'], \
        'Ringtime has to be smaller than interval'

    if args['--debug']:
        mesg = term.red(80*'=' + '\n' + '{:^80}\n' + 80*'=')
        print(mesg.format('DEBUG MODE - DO NOT USE DURING SHIFT'))

    handle_Skype.setup(args)
    handle_dim_stuff.setup(args)
    handle_QLA.setup(args)

    if args['<phonenumber>'] is not None:
        my_phone_number = handle_cli.check_phonenumber(args['<phonenumber>'])
    else:
        my_phone_number = handle_cli.enter_phone_number()
        my_phone_number = handle_cli.check_phonenumber(my_phone_number)

    while True:
        try:
            # the perform_checks() functions throw an FACTException
            # if the shifter needs to be called
            print('\n'+term.cyan(datetime.utcnow().strftime('%Y-%d-%m %H:%M:%s')))
            handle_dim_stuff.perform_checks()
            handle_QLA.perform_checks()
            print(term.green("Everything OK!"))
            time.sleep(args['--interval'])
        except FACTException as e:
            print(type(e), ":\n", e)
            handle_Skype.call(my_phone_number)
            time.sleep(args['--interval'])
        except Exception as e:
            if args['--debug']:
                raise
            else:
                print(e)
                handle_Skype.call(my_phone_number)
                time.sleep(args['--interval'])



if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        pass
