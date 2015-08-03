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
import handle_cli
import handle_Skype
import handle_telegram
from fact_exceptions import FACTException, QLAException
from docopt import docopt

from threading import Event
from collections import deque


def main(stop_event):
    term = Terminal()
    args = docopt(__doc__)

    args['--interval'] = float(args['--interval'])
    args['--ringtime'] = float(args['--ringtime'])
    assert args['--ringtime'] < args['--interval'], \
        'Ringtime has to be smaller than interval'

    if args['--debug']:
        mesg = term.red(80*'=' + '\n' + '{:^80}\n' + 80*'=')
        print(mesg.format('DEBUG MODE - DO NOT USE DURING SHIFT'))

    # handle_Skype.setup(args)
    # args = handle_cli.setup(args)
    # args['--telegram'] = handle_telegram.setup(args['--telegram'])

    from checks import Alert
    alert = Alert(queue=deque(),
                  interval=args['--interval'],
                  stop_event=stop_event
                  )

    if not args['--debug']:
        from checks.dim import MainJsStatusCheck
        check_mainjs = MainJsStatusCheck(
            alert.queue,
            args['--interval'],
            stop_event,
        )
        check_mainjs.start()

    from checks.dim import WeatherCheck
    check_weather = WeatherCheck(alert.queue, args['--interval'], stop_event)
    check_weather.start()

    from checks.dim import CurrentCheck
    check_currents = CurrentCheck(alert.queue, args['--interval'], stop_event)
    check_currents.start()

    alert.start()

    while True:
        try:
            time.sleep(10)
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
        stop_event = Event()
        main(stop_event)
    except (KeyboardInterrupt, SystemExit):
        stop_event.set()
