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
import time
from threading import Event
import logging
from docopt import docopt
from collections import deque
import blessings
import pkg_resources

from . import checks
from .checks import qla as qla
from .checks import webdim as webdim
from . import communication as com
from .config import config
from . import tools
from . import cli


__version__ = pkg_resources.require('shifthelper')[0].version
logdir = os.path.join(os.environ['HOME'], '.shifthelper')
if not os.path.exists(logdir):
    os.makedirs(logdir)

log = logging.getLogger('shift_helper')
log.setLevel(logging.DEBUG)
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

qla_filename = os.path.join(
    os.environ['HOME'],
    '.shifthelper',
    'plots/qla.png',
)

def main():
    log.info('shift helper started')
    log.info('version: {}'.format(__version__))

    args = docopt(
        __doc__,
        version=__version__,
    )
    term = blessings.Terminal()
    stop_event = Event()

    if args['--debug']:
        mesg = term.red(80*'=' + '\n' + '{:^80}\n' + 80*'=')
        print(mesg.format('DEBUG MODE - DO NOT USE DURING SHIFT'))
        log.setLevel(logging.DEBUG)
        log.debug('started shift helper in debug mode')

    if args['--no-call']:
        Caller = com.NoCaller
    else:
        Caller = com.TwilioInterface

    caller = Caller(phone_number=args['<phone_number>'])
    #telegram = com.TelegramInterface(config['telegram']['token'])
    telegram = None

    qla_data = {}
    system_status = {}

    try:
        check_weather = webdim.WeatherCheck(
            alert.queue,
            60,  # seconds
            stop_event,
            qla_data,
            system_status,
        )        

        check_rel_camera_temp = webdim.RelativeCameraTemperatureCheck(
            alert.queue,
            60,  # seconds
            stop_event,
            qla_data,
            system_status,
        )
        

        check_currents = webdim.CurrentCheck(
            alert.queue,
            60,   # seconds
            stop_event,
            qla_data,
            system_status,
        )
        

        flare_alert = qla.FlareAlert(
            alert.queue,
            300,   # seconds
            stop_event,
            qla_data,
            system_status,
        )

        for check in checks.Check.instances:
            check.start()
        

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
        queue = deque()
        while True:        
            if len(queue) > 0:
                caller.place_call()
                while len(queue) > 0:
                    message = queue.popleft()
                    log.warning(message)
                    telegram.send_message(message)
                    if 'Source' in message:
                        with open(qla_filename, 'rb') as img:
                            telegram.send_image(img)
            time.sleep(5)

    except (KeyboardInterrupt, SystemExit):
        stop_event.set()
        log.info('Exit')


if __name__ == '__main__':
    main()
