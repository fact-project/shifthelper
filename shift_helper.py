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
from blessings import Terminal
import logging
from tools import night
import os
from docopt import docopt
from threading import Event
from collections import deque
from ConfigParser import SafeConfigParser

from communication import SkypeInterface, TelegramInterface
import cli

# setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')
log = logging.getLogger('shift_helper')
log.setLevel(logging.INFO)
logfile = 'logs/shifthelper_{:%Y-%m-%d}.log'.format(night())
logfile_handler = logging.FileHandler(filename=logfile)
logfile_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt='%(asctime)s -%(levelname)s- %(message)s',
    datefmt='%H:%M:%S',
)
formatter.converter = time.gmtime  # use utc in log
logfile_handler.setFormatter(formatter)
log.addHandler(logfile_handler)

def read_config_file(config_file_name):
    config = SafeConfigParser()
    list_of_successfully_parsed_files = config.read(config_file_name)
    if config_file_name not in list_of_successfully_parsed_files:
        raise Exception('Can not find a config file named: '+config_file_name)
    return config

def main(stop_event):

    config = read_config_file('config.ini')

    term = Terminal()

    if args['--debug']:
        mesg = term.red(80*'=' + '\n' + '{:^80}\n' + 80*'=')
        print(mesg.format('DEBUG MODE - DO NOT USE DURING SHIFT'))
        log.setLevel(logging.DEBUG)
        log.debug('started shift helper in debug mode')

    print(term.cyan('Skype Setup'))
    #os.environ['DISPLAY'] = config.get('skype', 'display')
    skype = SkypeInterface(
        args['<phonenumber>'],
        config.getfloat('caller', 'ringtime'),
    )
    cli.check_phonenumber(skype)
    log.info('Using phonenumber: {}'.format(skype.phonenumber))

    print(term.cyan('\nTelegram Setup'))
    telegram = None
    if cli.ask_user('Do you want to use Telegram to receive notifications?'):
        telegram = TelegramInterface(config.get('telegram', 'token'))
        log.info('Using Telegram')

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
        from checks.webdim import MainJsStatusCheck
        check_mainjs = MainJsStatusCheck(
            alert.queue,
            config.getint('checkintervals', 'mainjs'),
            stop_event,
            qla_data,
            system_status,
        )
        check_mainjs.start()

    from checks.webdim import WeatherCheck
    check_weather = WeatherCheck(
        alert.queue,
        config.getint('checkintervals', 'weather'),
        stop_event,
        qla_data,
        system_status,
    )
    check_weather.start()

    from checks.webdim import RelativeCameraTemperatureCheck
    check_rel_camera_temp = RelativeCameraTemperatureCheck(
        alert.queue,
        config.getint('checkintervals', 'weather'),
        stop_event,
        qla_data,
        system_status,
    )
    check_rel_camera_temp.start()
    
    from checks.webdim import RelativeCameraHumidityCheck
    check_rel_camera_hum = RelativeCameraHumidityCheck(
        alert.queue,
        config.getint('checkintervals', 'weather'),
        stop_event,
        qla_data,
        system_status,
    )
    check_rel_camera_hum.start()

    from checks.webdim import CurrentCheck
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
