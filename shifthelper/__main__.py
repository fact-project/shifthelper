#!/usr/bin/env python
# coding: utf-8
import os
import json
import logging
import time
from custos import Custos, levels
from custos import TelegramNotifier, LogNotifier, IntervalCheck
from .notifiers import FactTwilioNotifier

from . import checks
from .tools.whosonshift import whoisonshift
from .tools import config

dot_shifthelper_dir = os.path.join(os.environ['HOME'], '.shifthelper')
os.makedirs(dot_shifthelper_dir, exist_ok=True)

logfile_handler = logging.handlers.TimedRotatingFileHandler(
    filename=os.path.join(dot_shifthelper_dir, 'shifthelper.log'), 
    when='D', interval=1,  # roll over every day.
    backupCount=300,       # keep 300 days back log
    utc=True
)
logfile_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt='%(asctime)s - %(levelname)s - %(name)s | %(message)s',
)
formatter.converter = time.gmtime  # use utc in log
logfile_handler.setFormatter(formatter)

log = logging.getLogger("custos")
log.setLevel(logging.DEBUG)
log.addHandler(logfile_handler)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logfile_handler)

def telegram_book(category):
    return ['123665317']
    return [whoisonshift().iloc[0].telegram_id]

def main():
    with Custos(
            checks=[
                checks.MainJsStatusCheck(interval=60),
                checks.HumidityCheck(interval=60),
                checks.WindSpeedCheck(interval=60),
                checks.WindGustCheck(interval=60),
                checks.MedianCurrentCheck(interval=60),
                checks.MaximumCurrentCheck(interval=60),
                checks.RelativeCameraTemperatureCheck(interval=60),
            ],
            notifiers=[
                FactTwilioNotifier(
                    sid=config['twilio']['sid'],
                    auth_token=config['twilio']['auth_token'],
                    twilio_number=config['twilio']['number'],
                    ring_time=10,
                    recipients=phone_book,
                    level=levels.WARNING,
                ),
                TelegramNotifier(
                    token=config['telegram']['token'],
                    recipients=telegram_book,
                    level=levels.INFO,
                ),
            ],
            ) as custos:
        custos.run()
