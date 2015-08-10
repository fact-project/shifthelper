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
'''
from __future__ import print_function
import time
from datetime import datetime
from blessings import Terminal
import logging
import fact
import os
from docopt import docopt
from threading import Event
from collections import deque
from traceback import format_exc
from ConfigParser import SafeConfigParser

from communication import SkypeInterface, TelegramInterface
import cli

# setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')
log = logging.getLogger('shift_helper')
logfile = logging.FileHandler(
    filename='logs/shifthelper_{:%Y-%m-%d}.log'.format(fact.night()),
)
logfile.setLevel(logging.INFO)
formatter = logging.Formatter(
    format='%(asctime)s -%(levelname)s- %(message)s',
    datefmt='%H:%M:%S',
)
logfile.setFormatter(formatter)
log.addHandler(logfile)



def main(stop_event):

    config = SafeConfigParser()
    config.read('config.ini')

    term = Terminal()

    if args['--debug']:
        mesg = term.red(80*'=' + '\n' + '{:^80}\n' + 80*'=')
        print(mesg.format('DEBUG MODE - DO NOT USE DURING SHIFT'))
        log.setLevel(logging.DEBUG)
        log.debug('started shift helper in debug mode')

    print(term.cyan('Skype Setup'))
    skype = SkypeInterface(
        args['<phonenumber>'],
        config.getfloat('caller', 'ringtime'),
    )
    cli.check_phonenumber(skype)
    log.info('Using phonenumber: {}'.format(skype.phonenumber))

    print(term.cyan('\nTelegram Setup'))
    if cli.ask_telegram() is True:
        telegram = TelegramInterface(config.get('telegram', 'token'))
        log.info('Using Telegram')
    else:
        telegram = None


    qla_data = {}
    system_status = {}

    from checks import Alert
    alert = Alert(queue=deque(),
                  interval=5,
                  stop_event=stop_event,
                  caller=skype,
                  messenger=telegram,
                  logger=log,
                  )

    if not args['--debug']:
        from checks.dim import MainJsStatusCheck
        check_mainjs = MainJsStatusCheck(
            alert.queue,
            config.getint('checkintervals', 'mainjs'),
            stop_event,
            qla_data,
            system_status,
        )
        check_mainjs.start()

    from checks.dim import WeatherCheck
    check_weather = WeatherCheck(
        alert.queue,
        config.getint('checkintervals', 'weather'),
        stop_event,
        qla_data,
        system_status,
    )
    check_weather.start()

    from checks.dim import CurrentCheck
    check_currents = CurrentCheck(
        alert.queue,
        config.getint('checkintervals', 'currents'),
        stop_event,
        qla_data,
        system_status,
    )
    check_currents.start()

    from checks.qla import FlareAlert
    flare_alert = FlareAlert(
        alert.queue,
        config.getint('checkintervals', 'qla'),
        stop_event,
        qla_data,
        system_status,
    )
    flare_alert.start()

    log.info('All checkers are running.')
    status = cli.StatusDisplay(qla_data, system_status, stop_event)

    alert.start()
    time.sleep(5)
    status.start()

    log.info('Entering main loop.')
    while True:
        time.sleep(10)

if __name__ == '__main__':
    args = docopt(__doc__)
    try:
        stop_event = Event()
        main(stop_event)
    except (KeyboardInterrupt, SystemExit):
        stop_event.set()
        log.info('Exit')
