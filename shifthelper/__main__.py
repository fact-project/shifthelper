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
    return [whoisonshift().telegram_id]


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
    auth=(
        config['webservice']['user'],
        config['webservice']['password']),
)

log = LogNotifier(level=levels.DEBUG, recipients=['all'])


def main():
    with Custos(
            checks=[
                checks.ShifterOnShift(interval=300),
                checks.MainJsStatusCheck(interval=300),
                checks.WindSpeedCheck(interval=300),
                checks.WindGustCheck(interval=300),
                checks.MedianCurrentCheck(interval=300),
                checks.MaximumCurrentCheck(interval=300),
                checks.RelativeCameraTemperatureCheck(interval=300),
                checks.BiasNotOperatingDuringDataRun(interval=300),
                checks.BiasChannelsInOverCurrent(interval=300),
                checks.BiasVoltageNotAtReference(interval=300),
                checks.ContainerTooWarm(interval=300),
                checks.DriveInErrorDuringDataRun(interval=300),
                checks.BiasVoltageOnButNotCalibrated(interval=300),
                checks.DIMNetworkNotAvailable(interval=300),
                checks.NoDimCtrlServerAvailable(interval=300),
                checks.TriggerRateLowForTenMinutes(interval=300),
                checks.IsUserAwakeBeforeShutdown(interval=300),
                checks.ParkingChecklistFilled(interval=300),
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
