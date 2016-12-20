#!/usr/bin/env python
# coding: utf-8
import sys
from custos import Custos, levels
from custos import TelegramNotifier, LogNotifier
from custos import HTTPNotifier
from .notifiers import FactTwilioNotifier

from .tools.shift import get_current_shifter
from .tools import config
from .logging import config_logging
from .checks import FactIntervalCheck, FlareAlertCheck
from . import conditions
from .categories import CATEGORY_SHIFTER, CATEGORY_DEVELOPER

config_logging(to_console=True)


def telegram_book(category):
    if category in ('check_error', CATEGORY_DEVELOPER):
        return [config['developer']['telegram_id']]
    try:
        telegram_id = get_current_shifter().telegram_id
    except IndexError:
        return []

    return [telegram_id] if telegram_id is not None else []


twilio = FactTwilioNotifier(
    sid=config['twilio']['sid'],
    auth_token=config['twilio']['auth_token'],
    twilio_number=config['twilio']['number'],
    ring_time=45,
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
        config['webservice']['password']
    ),
)

log = LogNotifier(level=levels.DEBUG, recipients=['all'])


def main():
    with Custos(
            checks=[
                FlareAlertCheck(category=CATEGORY_SHIFTER, interval=300),
                FactIntervalCheck(
                    name='DummyAlert',
                    interval=60,
                    checklist=[
                        conditions.is_dummy_alert_by_shifter,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='SmartFactUpToDate',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_smartfact_outdatet,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='MAGICWeatherUpToDate',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_magic_weather_outdatet,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='ShifterOnShift',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_nobody_on_shift,
                    ],
                    category=CATEGORY_DEVELOPER
                ),
                FactIntervalCheck(
                    name='MainJsStatusCheck',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_mainjs_not_running
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='WindSpeedCheck',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_high_windspeed,
                        conditions.is_not_parked,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='WindGustCheck',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_high_windgusts,
                        conditions.is_not_parked,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='MedianCurrentCheck',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_median_current_high,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='MaximumCurrentCheck',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_maximum_current_high,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='RelativeCameraTemperatureCheck',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_rel_camera_temperature_high,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='BiasNotOperatingDuringDataRun',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_bias_not_operating,
                        conditions.is_data_run,
                        conditions.is_data_taking,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='BiasChannelsInOverCurrent',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_overcurrent,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='BiasVoltageNotAtReference',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_bias_voltage_not_at_reference,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='ContainerTooWarm',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_container_too_warm,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='DriveInErrorDuringDataRun',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_drive_error,
                        conditions.is_data_run,
                        conditions.is_data_taking,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='BiasVoltageOnButNotCalibrated',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_voltage_on,
                        conditions.is_feedback_not_calibrated,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='DIMNetworkNotAvailable',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_dim_network_down,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='NoDimCtrlServerAvailable',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_no_dimctrl_server_available,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='IsUserAwakeBeforeShutdown',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_20minutes_or_less_before_shutdown,
                        conditions.is_nobody_awake,
                    ],
                    category=CATEGORY_SHIFTER
                ),
                FactIntervalCheck(
                    name='ParkingChecklistFilled',
                    checklist=[
                        conditions.is_no_shift_at_the_moment,
                        conditions.is_last_shutdown_already_10min_past,
                        conditions.is_checklist_not_filled,
                    ],
                    category=CATEGORY_DEVELOPER
                ),
                FactIntervalCheck(
                    name='TriggerRateLowForTenMinutes',
                    checklist=[
                        conditions.is_shift_at_the_moment,
                        conditions.is_data_taking,
                        conditions.is_trigger_rate_low_for_ten_minutes,
                    ],
                    category=CATEGORY_SHIFTER
                ),
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
