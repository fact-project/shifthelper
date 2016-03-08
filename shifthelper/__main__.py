#!/usr/bin/env python
# coding: utf-8
'''
This script is intended to call the shifter
if security or flare alert limits are reached.
Please do not accept or deny the call as this will
create costs for us. Just let it ring.
<phone_number> can either be a real phone_number or a twilio account.

Logs are stored in ~/.shifthelper

Usage:
    shift_helper.py [<phone_number>] [options]

Options
    --debug       Start the program in debug mode,
                  DO NOT USE ON SHIFT!
                  Programming errors are raised normally
                  and dimctrl status will not be checked for a running Main.js
    --version     Show version.
    --no-call     FOR DEBUGGING ONLY. Omit every call.
'''
from __future__ import print_function, absolute_import
import os
from os.path import expanduser
import time
from threading import Event
import logging
from docopt import docopt
from collections import deque
import pkg_resources

from . import tools, cli
from . import Alert, TelegramInterface
from . import (
    MainJsStatusCheck,
    WeatherCheck,
    RelativeCameraTemperatureCheck,
    CurrentCheck,
    FlareAlert,
)

__version__ = pkg_resources.require('shifthelper')[0].version
# setup logging
logdir = os.path.join(expanduser('~'), '.shifthelper')
if not os.path.exists(logdir):
    os.makedirs(logdir)

log = logging.getLogger('shift_helper')
log.setLevel(logging.INFO)
logfile_path = os.path.join(
    logdir, 'shifthelper_{:%Y-%m-%d}.log'.format(tools.night()),
)
logfile_handler = logging.FileHandler(filename=logfile_path)
logfile_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt='%(asctime)s - %(levelname)s - %(name)s | %(message)s',
    datefmt='%H:%M:%S',
)
formatter.converter = time.gmtime  # use utc in log
logfile_handler.setFormatter(formatter)
log.addHandler(logfile_handler)
logging.getLogger('py.warnings').addHandler(logfile_handler)
logging.captureWarnings(True)


def main():
    log.info('shift helper started')
    log.info('version: {}'.format(__version__))

    args = docopt(
        __doc__,
        version=__version__,
    )
    stop_event = Event()

    print(80 * '=')
    print('Welcome to the shift_helper!')
    print(80 * '=')

    config = tools.read_config_file()

    if args['--debug']:
        mesg = 80*'=' + '\n' + '{:^80}\n' + 80*'='
        print(mesg.format('DEBUG MODE - DO NOT USE DURING SHIFT'))
        log.setLevel(logging.DEBUG)
        log.debug('started shift helper in debug mode')

    if args['--no-call']:
        from . import NoCaller as Caller
    else:
        from . import TwilioInterface as Caller
        print('Twilio Phone Setup')

    caller = Caller(
        args['<phone_number>'],
        config.getint('caller', 'ringtime'),
        config.get('twilio', 'sid'),
        config.get('twilio', 'auth_token'),
        config.get('twilio', 'number'),
    )
    caller.check_phone_number()

    log.info('Using phone_number: {}'.format(caller.phone_number))

    print('\nTelegram Setup')
    telegram = None
    if cli.ask_user('Do you want to use Telegram to receive notifications?'):
        telegram = TelegramInterface(config.get('telegram', 'token'))
        log.info('Using Telegram')

    print(
        (
            "\n"
            "    Thank you for using shift_helper tonight.\n"
            "    -----------------------------------------\n"
            "    We hope it was a pleasant experience.\n"
            "    Please consider sending your log-file:\n"
            "    {}\n".format(logfile_path) +
            "    to: neised@phys.ethz.ch for future improvements\n"
        )
    )

    qla_data = {}
    system_status = {}

    try:
        alert = Alert(
            queue=deque(),
            interval=5,
            stop_event=stop_event,
            caller=caller,
            messenger=telegram,
            logger=log,
        )

        if not args['--debug']:
            check_mainjs = MainJsStatusCheck(
                alert.queue,
                config.getint('checkintervals', 'mainjs'),
                stop_event,
                qla_data,
                system_status,
            )
            check_mainjs.start()

        check_weather = WeatherCheck(
            alert.queue,
            config.getint('checkintervals', 'weather'),
            stop_event,
            qla_data,
            system_status,
        )
        check_weather.start()

        check_rel_camera_temp = RelativeCameraTemperatureCheck(
            alert.queue,
            config.getint('checkintervals', 'weather'),
            stop_event,
            qla_data,
            system_status,
        )
        check_rel_camera_temp.start()

        check_currents = CurrentCheck(
            alert.queue,
            config.getint('checkintervals', 'currents'),
            stop_event,
            qla_data,
            system_status,
        )
        check_currents.start()

        flare_alert = FlareAlert(
            alert.queue,
            config.getint('checkintervals', 'qla'),
            stop_event,
            qla_data,
            system_status,
        )
        flare_alert.start()

        log.info('All checkers are running.')
        status = cli.StatusDisplay(
            qla_data,
            system_status,
            stop_event,
            logfile_path,
        )

        alert.start()
        status.start()

        log.info('Entering main loop.')
        while True:
            time.sleep(10)

    except (KeyboardInterrupt, SystemExit):
        stop_event.set()
        log.info('Exit')


if __name__ == '__main__':
    main()
