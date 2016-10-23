from custos import IntervalCheck
from . import retry_smart_fact_crawler as sfc
from .tools.is_shift import is_shift_at_the_moment
import requests
from requests.exceptions import RequestException
from abc import ABCMeta, abstractmethod

import pandas as pd
from datetime import timedelta, datetime
import re as regex

from retrying import retry

import logging

log = logging.getLogger(__name__)


class FactIntervalCheck(IntervalCheck, metaclass=ABCMeta):

    def check(self):
        if is_shift_at_the_moment():
            text = self.inner_check()
            if text is not None:
                try:
                    acknowledged = self.all_recent_alerts_acknowledged()
                except RequestException:
                    log.exception('Could not check acknowledged alerts')
                    acknowledged = False

                if acknowledged is True:
                    self.info(text)
                else:
                    self.warning(text)
        else:
            debug_log_msg = self.__class__.__name__ + '.check():'
            debug_log_msg += " - no shift at the moment."
            log.debug(debug_log_msg)

    @retry(stop_max_delay=30000,  # 30 seconds max
           wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
           wait_exponential_max=1000,  # but wait 1 second per try maximum
           )
    def all_recent_alerts_acknowledged(self):
        all_alerts = requests.get('http://localhost:5000/alerts').json()
        if not all_alerts:
            return False

        now = datetime.utcnow()
        all_alerts = pd.DataFrame(all_alerts)
        all_alerts['timestamp'] = pd.to_datetime(all_alerts.timestamp, utc=True)

        my_alerts = all_alerts[all_alerts.check == self.__class__.__name__]
        if my_alerts.empty:
            return False

        my_recent_alerts = my_alerts[(now - my_alerts.timestamp) < timedelta(minutes=10)]
        if my_recent_alerts.empty:
            return False

        if not my_recent_alerts.acknowledged.all():
            return False
        return True

    @abstractmethod
    def inner_check(self):
        pass


class MainJsStatusCheck(FactIntervalCheck):
    def inner_check(self):
        dim_control_status = sfc.status().dim_control
        log.debug("MainJsStatusCheck: dim_control_status:o{}".format(dim_control_status))
        if 'Running' not in dim_control_status:
            return 'Main.js is not running'


class HumidityCheck(FactIntervalCheck):
    def inner_check(self):
        lid_status = sfc.status().lid_control
        # this translation is a dirty hack,
        # and not guaranteed to work.
        lid_status_translation = {
            'Inconsistent': 'Closed',
            'Closed': 'Closed',
            'Open': 'Open',
            'PowerProblem': 'Open'
        }
        lid_status = lid_status_translation.get(lid_status, 'Unknown')

        humidity = sfc.weather().humidity.value
        log.debug(
            "HumidityCheck: humidity:{0} lid_status:{1}".format(humidity, lid_status)
        )
        if humidity >= 98 and lid_status == 'Open':
            return 'Humidity > 98% while Lid open'


def is_parked():
    az = sfc.drive_pointing().azimuth.value
    zd = sfc.drive_pointing().zenith_distance.value
    # is_locked = sfc.status().drive_control == 'Locked'
    # should is_locked be taken into account here?
    # pointing north is enough ...
    # but driving through north ... is not :-|
    return (-5 < az < 5) and (90 < zd)


def is_drive_error():
    drive_state = sfc.status().drive_control
    return drive_state in [
        'ERROR',
        'PositioningFailed',
        'OutOfRange',
        'InvalidCoordinates',
        'FATAL',
    ]


def is_data_taking():
    # if MCP::State::kTriggerOn ||MCP::State::kTakingData;
    # the state name strings, I took from dimctrl on newdaq, typing `st`
    return sfc.status().mcp in ['TakingData', 'TriggerOn']


def is_data_run():
    # fMcpConfigurationName=='data' || fMcpConfigurationName=='data-rt';
    # this fMcpConfigurationName seems to turn um in square brackets []
    # inside sfc.main_page().system_status, but I'm not sure yet.
    # yes it does: example:
    # sfc.main_page().system_status --> 'Idle [single-pe]'
    try:
        config_name = regex.search('\[(.*)\]', sfc.main_page().system_status).groups()[0]
        return config_name in ['data', 'data-rt']
    except IndexError:
        # regex did not match
        return False


def is_bias_not_operating():
    ''' in smartfact.cc this check is done as:
        fDimBiasControl.state() < BIAS::State::kRamping

        this is the list of states with their numbers:
        so we can explicitely describe, which ones we define as 'not operating'

     -256: Offline
       -1: NotReady (State machine not ready, events are ignored.)
        0: Ready (State machine ready to receive events.)
        1: Disconnected (Bias-power supply not connected via USB.)
        2: Connecting (Trying to establish USB connection to bias-power supply.)
        3: Initializing (USB connection to bias-power supply established, synchronizing USB stream.)
        4: Connected (USB connection to bias-power supply established.)
        5: Ramping (Voltage ramping in progress.)
        6: OverCurrent (At least one channel is in over current state.)
        7: VoltageOff (All voltages are supposed to be switched off.)
        8: NotReferenced (Internal reference voltage does not match last sent voltage.)
        9: VoltageOn (At least one voltage is switched on and all are at reference.)
       10: ExpertMode (Special (risky!) mode to directly send command to the bias-power supply.)
       11: Locked (Locked due to emergency shutdown, no commands accepted except UNLOCK.)
      256: ERROR (Common error state.)
    65535: FATAL (A fatal error occured, the eventloop is stopped.)
    '''
    bias_state = sfc.status().bias_control
    return bias_state in [
        'Offline',
        'NotReady',
        'Ready',
        'Disconnected',
        'Connecting',
        'Initializing',
        'Connected',
        'Locked',
        'ERROR',
        'FATAL',
    ]


def is_feedback_not_calibrated():
    feedback_state = sfc.status().feedback
    return feedback_state in [
        'Offline',
        'NotReady',
        'Ready',
        'DimNetworkNotAvailable',
        'Disconnected',
        'Connecting',
        'Connected',
    ]


class WindSpeedCheck(FactIntervalCheck):
    def inner_check(self):
        wind_speed = sfc.weather().wind_speed.value
        _is_parked = is_parked()
        log.debug("WindSpeedCheck: is_parked:{0}, wind_speed:{1}".format(_is_parked, wind_speed))
        if wind_speed >= 50 and not _is_parked:
            'Wind speed > 50 km/h and not parked'

class WindGustCheck(FactIntervalCheck):
    def inner_check(self):
        wind_gusts = sfc.weather().wind_gusts.value
        _is_parked = is_parked()
        log.debug("WindGustCheck: is_parked:{0}, wind_speed:{1}".format(_is_parked, wind_gusts))
        if wind_gusts >= 50 and not _is_parked:
            return 'Wind gusts > 50 km/h and not parked'

class MedianCurrentCheck(FactIntervalCheck):
    def inner_check(self):
        is_currents_calibrated = sfc.sipm_currents().calibrated
        median_current = sfc.sipm_currents().median_per_sipm.value
        log.debug("MedianCurrentCheck: is_currents_calibrated:{0}, median_current:{1}".format(is_currents_calibrated, median_current))
        if is_currents_calibrated:
            if median_current >= 115:
                return 'Median GAPD current > 115uA'

class MaximumCurrentCheck(FactIntervalCheck):
    def inner_check(self):
        is_currents_calibrated = sfc.sipm_currents().calibrated
        max_current = sfc.sipm_currents().max_per_sipm.value
        log.debug("MaximumCurrentCheck: is_currents_calibrated:{0}, max_current:{1}".format(is_currents_calibrated, max_current))
        if is_currents_calibrated:
            if max_current >= 160:
                return 'Maximum GAPD current > 160uA'

class RelativeCameraTemperatureCheck(FactIntervalCheck):
    def inner_check(self):
        relative_temperature = sfc.main_page().relative_camera_temperature.value
        log.debug('RelativeCameraTemperatureCheck: relative_temperature:{0}'.format(relative_temperature))
        if relative_temperature >= 15.0:
            return 'relative camera temperature > 15°C'


class BiasNotOperatingDuringDataRun(FactIntervalCheck):
    def inner_check(self):
        _is_bias_not_operating = is_bias_not_operating()
        _is_data_taking = is_data_taking()
        _is_data_run = is_data_run()
        log.debug('BiasNotOperatingDuringDataRun: '
            '_is_bias_not_operating:{0}, '
            '_is_data_taking:{1}, '
            '_is_data_run:{2}'.format(
            _is_bias_not_operating,
            _is_data_taking,
            _is_data_run))
        if (_is_bias_not_operating
                and _is_data_taking
                and _is_data_run):
            return 'Bias not operating during data run'


class BiasChannelsInOverCurrent(FactIntervalCheck):
    def inner_check(self):
        bias_state = sfc.status().bias_control
        log.debug('BiasChannelsInOverCurrent: bias_state:{}'.format(bias_state))
        if bias_state == 'OverCurrent':
            return 'Bias Channels in Over Current'


class BiasVoltageNotAtReference(FactIntervalCheck):
    def inner_check(self):
        bias_state = sfc.status().bias_control
        log.debug('BiasVoltageNotAtReference: bias_state:{}'.format(bias_state))
        if bias_state == 'NotReferenced':
            return 'Bias Voltage not at reference.'


class ContainerTooWarm(FactIntervalCheck):
    def inner_check(self):
        container_temperature = float(sfc.container_temperature().current.value)
        log.debug('ContainerTooWarm: container_temperature:{}'.format(container_temperature))
        if container_temperature > 42:
            return 'Container Temperature above 42 deg C'


class DriveInErrorDuringDataRun(FactIntervalCheck):
    def inner_check(self):
        _is_drive_error = is_drive_error()
        _is_data_taking = is_data_taking()
        _is_data_run = is_data_run()
        log.debug('DriveInErrorDuringDataRun: '
            '_is_drive_error:{0}, '
            '_is_data_taking:{1}, '
            '_is_data_run:{2}'.format(
                _is_drive_error,
                _is_data_taking,
                _is_data_run))
        if (_is_drive_error
                and _is_data_taking
                and _is_data_run
                ):
            return 'Drive in Error during Data run'


class BiasVoltageOnButNotCalibrated(FactIntervalCheck):
    def inner_check(self):
        is_voltage_on = sfc.status().bias_control == 'VoltageOn'
        _is_feedback_not_calibrated = is_feedback_not_calibrated()
        median_voltage = sfc.sipm_voltages().median.value
        log.debug('BiasVoltageOnButNotCalibrated: '
            'is_voltage_on:{0}, '
            '_is_feedback_not_calibrated:{1}, '
            'median_voltage:{2}'.format(
                is_voltage_on,
                _is_feedback_not_calibrated,
                median_voltage
                ))
        if (is_voltage_on
                and _is_feedback_not_calibrated
                and median_voltage > 3 # volt
                ):
            return 'Bias voltage switched on, but bias crate not calibrated'

class DIMNetworkNotAvailable(FactIntervalCheck):
    def inner_check(self):
        # can be checked this way according to:
        # https://trac.fact-project.org/browser/trunk/FACT%2B%2B/src/smartfact.cc#L3131
        dim_network_status = sfc.status().dim
        log.debug('DIMNetworkNotAvailable: {0}'.format(dim_network_status))
        if dim_network_status == 'Offline':
            return 'DIM network not available'

class NoDimCtrlServerAvailable(FactIntervalCheck):
    def inner_check(self):
        # Didn't find a clear way to check this, so I do:
        dim_control_status = sfc.status().dim_control
        log.debug('NoDimCtrlServerAvailable: dim_control_status:{0}'.format(dim_control_status))
        if dim_control_status in [
                'Offline',
                'NotReady',
                'ERROR',
                'FATAL',
                ]:
            return 'no dimctrl server available'


class TriggerRateLowForTenMinutes(FactIntervalCheck):
    history = pd.DataFrame()

    def inner_check(self):
        current_trigger_rate = sfc.trigger_rate().trigger_rate.value
        self._append_to_history(current_trigger_rate)
        self._remove_old_entries()

        df = pd.DataFrame(self.history)
        log.debug('TriggerRateLowForTenMinutes: trigger_rate_history:{0}'.format(df))
        if not df.empty and (df.rate < 1).all():
            return 'Trigger rate < 1/s for 10 minutes'

    def _append_to_history(self, rate):
        self.history = self.history.append([{'timestamp':datetime.utcnow(), 'rate':rate}])

    def _remove_old_entries(self):
        now = datetime.utcnow()
        self.history = self.history[(now - self.history.timestamp) < timedelta(minutes=10)]

