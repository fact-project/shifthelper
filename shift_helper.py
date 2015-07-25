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

    --ringtime=<N>  how long skype wil lett you phone ring [default: 20]

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
from fact_exceptions import FACTException, QLAException
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
    args = handle_cli.setup(args)

    args['--telegram'] = handle_telegram.setup(args['--telegram'])

    while True:
        try:
            # the perform_checks() functions throw an FACTException
            # if the shifter needs to be called
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            print('\n' + term.cyan(timestamp))
            handle_dim_stuff.perform_checks(debug=args['--debug'])
            handle_QLA.perform_checks()
            print(term.green("Everything OK!"))
            time.sleep(args['--interval'])
        except FACTException as e:
            mesg = e.__name__ + ":\n" + str(e)
            print(term.red(mesg))
            if args['--telegram']:
                handle_telegram.send_message(mesg)
                if isinstance(e, QLAException):
                    image = handle_QLA.get_image(e.source_key)
                    handle_telegram.send_image(image)
                    image.close()

            handle_Skype.call(args['<phonenumber>'])
            time.sleep(args['--interval'])
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            if args['--debug']:
                raise
            else:
                if args['--telegram']:
                    handle_telegram.send_message('Python Error')
                handle_Skype.call(args['<phonenumber>'])
                time.sleep(args['--interval'])


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        pass
