#!/usr/bin/env python
# coding: utf-8
'''
This script is intended to call the shifter
if security or flare alert limits are reached.
Please do not accept or deny the call as this will
create costs for us. Just let it ring.
<phone_number> can either be a real phone_number or a twilio account.

Usage:
    shift_helper.py [<phone_number>] [options]

Options
    --debug  Start the program in debug mode, DO NOT USE ON SHIFT!
             Programming errors are raised normally
             and dimctrl status will not be checked for a running Main.js
'''
from __future__ import print_function
import os
import time
from threading import Event
import logging
from docopt import docopt
from collections import deque
import blessings

from fact_shift_helper import *

# setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')
log = logging.getLogger('shift_helper')
log.setLevel(logging.INFO)
logfile = 'logs/shifthelper_{:%Y-%m-%d}.log'.format(tools.night())
logfile_handler = logging.FileHandler(filename=logfile)
logfile_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt='%(asctime)s -%(levelname)s- %(message)s',
    datefmt='%H:%M:%S',
)
formatter.converter = time.gmtime  # use utc in log
logfile_handler.setFormatter(formatter)
log.addHandler(logfile_handler)


def main(stop_event):
    config = tools.read_config_file('config.ini')

    term = blessings.Terminal()

    if args['--debug']:
        mesg = term.red(80*'=' + '\n' + '{:^80}\n' + 80*'=')
        print(mesg.format('DEBUG MODE - DO NOT USE DURING SHIFT'))
        log.setLevel(logging.DEBUG)
        log.debug('started shift helper in debug mode')

    print(term.cyan('Twilio Phone Setup'))

    caller = TwilioInterface(
        args['<phone_number>'],
        config.getint('caller', 'ringtime'),
        config.get('twilio', 'sid'),
        config.get('twilio', 'auth_token'),
        config.get('twilio', 'number'),
        )
    cli.check_phone_number(caller)
    log.info('Using phone_number: {}'.format(caller.phone_number))

    print(term.cyan('\nTelegram Setup'))
    telegram = None
    if cli.ask_user('Do you want to use Telegram to receive notifications?'):
        telegram = TelegramInterface(config.get('telegram', 'token'))
        log.info('Using Telegram')

    qla_data = {}
    system_status = {}

    class NoQueue(object):
        def append(self, something=None):
            pass

    dummy_queue_doing_nothing = NoQueue()
    
    alert = Alert(queue=deque(),
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

    check_rel_camera_hum = RelativeCameraHumidityCheck(
        alert.queue,
        config.getint('checkintervals', 'weather'),
        stop_event,
        qla_data,
        system_status,
    )
    check_rel_camera_hum.start()

    check_currents = CurrentCheck(
        alert.queue,
        config.getint('checkintervals', 'currents'),
        stop_event,
        qla_data,
        system_status,
    )
    check_currents.start()

    lidcam_response = LidCamCheck(
        dummy_queue_doing_nothing,
        config.getint('checkintervals', 'weather'),
        stop_event,
        qla_data,
        system_status,
    )
    lidcam_response.start()

    IRcam_response = IrCamCheck(
        dummy_queue_doing_nothing,
        config.getint('checkintervals', 'weather'),
        stop_event,
        qla_data,
        system_status,
    )
    IRcam_response.start()

    flare_alert = FlareAlert(
        alert.queue,
        config.getint('checkintervals', 'qla'),
        stop_event,
        qla_data,
        system_status,
    )
    flare_alert.start()

    log.info('All checkers are running.')
    status = cli.StatusDisplay(qla_data, system_status, stop_event, logfile)

    alert.start()
    status.start()

    log.info('Entering main loop.')
    while True:
        time.sleep(10)

if __name__ == '__main__':
    log.info('shift helper started')
    args = docopt(__doc__)
    try:
        stop_event = Event()
        main(stop_event)
    except (KeyboardInterrupt, SystemExit):
        stop_event.set()
        log.info('Exit')