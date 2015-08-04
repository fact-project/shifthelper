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
'''
from __future__ import print_function
import time
from datetime import datetime
from blessings import Terminal
import handle_cli
from docopt import docopt
from threading import Event
from collections import deque
from ConfigParser import SafeConfigParser

from communication import SkypeInterface, TelegramInterface


def main(stop_event):

    config = SafeConfigParser()
    config.read('config.ini')

    term = Terminal()
    args = docopt(__doc__)

    args['--interval'] = float(args['--interval'])
    args['--ringtime'] = float(args['--ringtime'])
    assert args['--ringtime'] < args['--interval'], \
        'Ringtime has to be smaller than interval'


    if args['--debug']:
        mesg = term.red(80*'=' + '\n' + '{:^80}\n' + 80*'=')
        print(mesg.format('DEBUG MODE - DO NOT USE DURING SHIFT'))

    print(term.cyan('Skype Setup'))
    skype = SkypeInterface(args['<phonenumber>'], args['--ringtime'])
    handle_cli.check_phonenumber(skype)

    print(term.cyan('\nTelegram Setup'))
    if handle_cli.ask_telegram() is True:
        telegram = TelegramInterface(config.get('telegram', 'token'))
    else:
        telegram = None

    from checks import Alert
    alert = Alert(queue=deque(),
                  interval=args['--interval'],
                  stop_event=stop_event,
                  caller=skype,
                  messenger=telegram,
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

    from checks.qla import FlareAlert
    flare_alert = FlareAlert(alert.queue, args['--interval'], stop_event)
    flare_alert.start()

    print('All checkers are running')
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
                skype.place_call(args['<phonenumber>'])
                time.sleep(args['--interval'])


if __name__ == '__main__':
    try:
        stop_event = Event()
        main(stop_event)
    except (KeyboardInterrupt, SystemExit):
        stop_event.set()
