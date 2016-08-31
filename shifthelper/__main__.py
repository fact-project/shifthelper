#!/usr/bin/env python
# coding: utf-8
'''
This script is intended to call the shifter
if security or flare alert limits are reached.
Please do not accept or deny the call as this will
create costs for us. Just let it ring.

Logs are stored in ~/.shifthelper

Usage:
    shift_helper.py [options]

Options
    --version     Show version.
'''


"""
caller

call can find out if shifter responded.

def alert_shifter
    until human responded:
      - try to call 1st shifter(ring time 40sec)
      - after 20sec try to call 1st shifter again(ring time 20sec)
      - after 5min try to call 2nd shifter(ring time 40sec)
      - after 20sec keep trying 2nd shifter.
      - after 

Do not forget to check the times of the .data pages in 
smarft fact
"""

import logging
from docopt import docopt
from . import checks
from . import communication as com
from .config import config
from . import __version__
import json
from .tools import logs_exception
from shifthelper.tools.whosonshift import whoisonshift
log = logging.getLogger(__name__)
from datetime import datetime, timedelta

@logs_exception("failed to alert shifter via phone")
def alert_via_phone():
    shifters = whoisonshift(clear_cache=True).iloc[0]
    phone_number = one_shifter["phone_mobile"].replace("-/ ","")
    log.debug("phone_number:"+str(phone_number))

    call = com.TwilioInterface(phone_number).place_call()
    log.debug(str(call))
    if call["answered_by"]:
        # test if human answered using something like:
        # "human" in call["answered_by"]
        log.debug("call answered by " + repr(call["answered_by"]))


@logs_exception("failed to alert shifter via telegram")
def alert_via_telegram(message):
    one_shifter = whoisonshift(clear_cache=True).iloc[0]
    telegram_chat_id = json.loads(one_shifter["telegram_json"])["telegram"]
    log.debug("telegram_chat_id:"+str(telegram_chat_id))
    telegram = com.TelegramInterface(telegram_chat_id)
    try:
        telegram.send_image(message.image)
    except AttributeError:
        telegram.send_message(message)


def main():
    log.info('shift helper started')
    log.info('version: {}'.format(__version__))
    args = docopt(__doc__, version=__version__)

    try:
        [CheckerClass(interval=60) for CheckerClass in checks.webdim.check_list]
        checks.qla.FlareAlert(interval=300)
        [check.start() for check in checks.Check.instances]
        
        log.info('All checkers are running.')
        log.info('Entering main loop.')
        while True:
            message = checks.Check.messages.get()
            log.warning(message)
            alert_via_phone()
            alert_via_telegram(message)

    except (KeyboardInterrupt, SystemExit):
        checks.Check.stop_event.set()
        log.info('Exit')


if __name__ == '__main__':
    main()
