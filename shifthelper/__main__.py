#!/usr/bin/env python
# coding: utf-8
import sys
from custos import Custos, levels
from custos import TelegramNotifier, LogNotifier
from custos import HTTPNotifier
from .notifiers import FactTwilioNotifier

from . import checks
from .tools.whosonshift import whoisonshift
from .tools import config
from .logging import config_logging

config_logging(to_console=False)


def telegram_book(category):
    return [config['developer']['telegram_id']]
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
    recipients=[config['webservice']['post-url']],
    auth=(config['webservice']['user'],
        config['webservice']['password']),
)

log = LogNotifier(level=levels.DEBUG, recipients=['all'])


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
                checks.BiasNotOperatingDuringDataRun(interval=60),
                checks.BiasChannelsInOverCurrent(interval=60),
                checks.BiasVoltageNotAtReference(interval=60),
                checks.ContainerTooWarm(interval=60),
                checks.DriveInErrorDuringDataRun(interval=60),
                checks.BiasVoltageOnButNotCalibrated(interval=60),
                checks.DIMNetworkNotAvailable(interval=60),
                checks.NoDimCtrlServerAvailable(interval=60),
                checks.TriggerRateLowForTenMinutes(interval=60),
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
