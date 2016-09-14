#!/usr/bin/env python
# coding: utf-8
import sys, json
from custos import Custos, levels
from custos import TelegramNotifier, LogNotifier, IntervalCheck
from custos import HTTPNotifier
from .notifiers import FactTwilioNotifier

from . import checks
from .tools.whosonshift import whoisonshift
from .tools import config
from .logging import config_logging

config_logging(to_console=False)

def telegram_book(category):
    return ['123665317']
    return [whoisonshift().iloc[0].telegram_id]

twilio = FactTwilioNotifier(
                    sid=config['twilio']['sid'],
                    auth_token=config['twilio']['auth_token'],
                    twilio_number=config['twilio']['number'],
                    ring_time=10,
                    level=levels.WARNING,
                )
telegram = TelegramNotifier(
                    token=config['telegram']['token'],
                    recipients=telegram_book,
                    level=levels.INFO,
                )
http = HTTPNotifier(
                    level=levels.WARNING,
                    recipients=['http://localhost:5000/alerts'],
                    auth=('fact', 'test'),
                )

log = LogNotifier(
                    level=levels.DEBUG,
                    recipients=['all'],
                )



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
                twilio,
                telegram,
                http,
                log,
            ],
            ) as custos:
        try:
            custos.run()
        except (KeyboardInterrupt, SystemError):
            sys.exit(0)
