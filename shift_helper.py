#!/usr/bin/env python
# coding: utf-8
'''
This script is intended to call the shifter
if security or flare alert limits are reached.
Please do not accept or deny the call as this will
create costs for us. Just let it ring.
<phonenumber> can either be a real phonenumber or a skype account.

Usage:
    shift_helper.py [<phonenumber>] [options]

Options
    --debug  Start the program in debug mode, DO NOT USE ON SHIFT!
             Programming errors are raised normally
             and dimctrl status will not be checked for a running Main.js

    --interval=<N>  The interval between the cecks in seconds [default: 60]

    --ringtime=<N>  how long skype wil lett you phone ring [default: 10]

    --telegram  Get Telegram messages with errors from the factShiftHelperBot
'''
from __future__ import print_function
import time
from datetime import datetime
from blessings import Terminal
import handle_QLA
import handle_dim_stuff
import handle_cli
import handle_Skype
import handle_telegram
from fact_exceptions import FACTException
from docopt import docopt


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
    args = handle_cli.setup(args)

    if not args['--telegram']:
        use_tg = raw_input('Do you want to use Telegram to get error messages?')
        if use_tg.lower()[0] == 'y':
            args['--telegram'] = True

    if args['--telegram']:
        args['--telegram'] == handle_telegram.setup()

    while True:
        try:
            # the perform_checks() functions throw an FACTException
            # if the shifter needs to be called
            timestamp = datetime.utcnow().strftime('%Y-%d-%m %H:%M:%S')
            print('\n' + term.cyan(timestamp))
            handle_dim_stuff.perform_checks(debug=args['--debug'])
            handle_QLA.perform_checks()
            print(term.green("Everything OK!"))
            time.sleep(args['--interval'])
        except FACTException as e:
            mesg = e.__name__ + ":\n" + str(e)
            print(term.red(mesg))
            handle_telegram.send_message(mesg)
            handle_Skype.call(args['<phonenumber>'])
            time.sleep(args['--interval'])
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            if args['--debug']:
                raise
            else:
                print(e)
                handle_telegram.send_message('Python Error')
                handle_Skype.call(args['<phonenumber>'])
                time.sleep(args['--interval'])


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        pass
