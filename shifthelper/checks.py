from operator import attrgetter
from custos import IntervalCheck, levels, Message
from . import retry_smart_fact_crawler as sfc
from .tools.is_shift import is_shift_at_the_moment, get_next_shutdown, get_last_shutdown
from .tools.whosonshift import whoisonshift
from .tools import config, get_last_parking_checklist_entry
import requests
from requests.exceptions import RequestException
from abc import ABCMeta, abstractmethod

import pandas as pd
from datetime import timedelta, datetime
import re as regex

from retrying import retry, RetryError

import logging

log = logging.getLogger(__name__)


CATEGORY_SHIFTER = 'shifter'
CATEGORY_DEVELOPER = 'developer'

class MessageMixin:
    def message(self, checklist, **kwargs):
        return Message(
            text=' and \n'.join(map(attrgetter('__doc__'), checklist)),
            level=message_level(self.__class__.__name__),
            **kwargs
            )

@retry(stop_max_delay=30000,  # 30 seconds max
       wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
       wait_exponential_max=1000,  # but wait 1 second per try maximum
       )
def all_recent_alerts_acknowledged(checkname):
    '''
    have a look at shifthelper webinterface page and see if the
    user has already acknowledged all the alerts from the given
    checkname.

    In case we cannot even reach the webinterface, we have to assume the
    user also cannot reach the website, so nothing will be acknowledged.
    So in that case we simply return False as well
    '''
    try:
        all_alerts = requests.get(config['webservice']['post-url']).json()
    except RequestException:
        log.warning('Could not check acknowledged alerts')
        return False

    if not all_alerts:
        return False

    now = datetime.utcnow()
    all_alerts = pd.DataFrame(all_alerts)
    all_alerts['timestamp'] = pd.to_datetime(all_alerts.timestamp, utc=True)

    my_alerts = all_alerts[all_alerts.check == checkname]
    if my_alerts.empty:
        return False

    my_recent_alerts = my_alerts[(now - my_alerts.timestamp) < timedelta(minutes=10)]
    if my_recent_alerts.empty:
        return False

    if not my_recent_alerts.acknowledged.all():
        return False
    return True

def message_level(checkname):
    '''
    return the message severity level for a certain check,
    based on whether all the alerts have been acknowledged or not
    '''
    if all_recent_alerts_acknowledged(checkname):
        return levels.INFO
    else:
        return levels.WARNING

def is_mainjs_not_running():
    '''Main.js is not running'''
    dim_control_status = sfc.status().dim_control
    log.debug("MainJsStatusCheck: dim_control_status: {}".format(dim_control_status))
    return 'Running' not in dim_control_status


class MainJsStatusCheck(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [is_shift_at_the_moment, is_mainjs_not_running]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)

def is_lid_open():
    '''The Lid is Open'''
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
    return lid_status == 'Open'


def is_humidity_high():
    '''Humidity > 98%'''
    return sfc.weather().humidity.value >= 98


class HumidityCheck(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_humidity_high,
            is_lid_open,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)


def is_not_parked():
    ''' Telescope not parked '''
    az = sfc.drive_pointing().azimuth.value
    zd = sfc.drive_pointing().zenith_distance.value
    # is_locked = sfc.status().drive_control == 'Locked'
    # should is_locked be taken into account here?
    # pointing north is enough ...
    # but driving through north ... is not :-|
    return not ((-5 < az < 5) and (90 < zd))


def is_drive_error():
    ''' DriveCtrl in some error state '''
    drive_state = sfc.status().drive_control
    return drive_state in [
        'ERROR',
        'PositioningFailed',
        'OutOfRange',
        'InvalidCoordinates',
        'FATAL',
    ]


def is_data_taking():
    '''is taking data'''
    # if MCP::State::kTriggerOn ||MCP::State::kTakingData;
    # the state name strings, I took from dimctrl on newdaq, typing `st`
    return sfc.status().mcp in ['TakingData', 'TriggerOn']


def is_data_run():
    '''is doing physics data run'''
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
    '''bias not operating'''

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
    ''' feedback is not calibrated '''
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

def is_high_windspeed():
    '''windspeed > 50km/h'''
    return sfc.weather().wind_speed.value >= 50

def is_high_windgusts():
    '''Wind gusts > 50 km/h'''
    return sfc.weather().wind_gusts.value >= 50

def is_median_current_high():
    '''Median GAPD current > 115uA'''
    is_currents_calibrated = sfc.sipm_currents().calibrated
    median_current = sfc.sipm_currents().median_per_sipm.value
    return is_currents_calibrated and median_current >= 115

def is_maximum_current_high():
    '''Maximum GAPD current > 160uA'''
    is_currents_calibrated = sfc.sipm_currents().calibrated
    max_current = sfc.sipm_currents().max_per_sipm.value
    return is_currents_calibrated and max_current >= 160

def is_rel_camera_temperature_high():
    '''relative camera temperature > 15°C'''
    relative_temperature = sfc.main_page().relative_camera_temperature.value
    return relative_temperature >= 15.0

def is_overcurrent():
    '''Bias Channels in Over Current'''
    return sfc.status().bias_control == 'OverCurrent'

def is_bias_voltage_not_at_reference():
    '''Bias Voltage not at reference'''
    return sfc.status().bias_control == 'NotReferenced'

def is_container_too_warm():
    '''Container Temperature above 42 °C'''
    container_temperature = float(sfc.container_temperature().current.value)
    return container_temperature > 42

def is_voltage_on():
    '''Bias Voltage is On'''
    median_voltage = sfc.sipm_voltages().median.value
    return sfc.status().bias_control == 'VoltageOn' and median_voltage > 3

def is_dim_network_down():
    '''DIM network not available'''
    # can be checked this way according to:
    # https://trac.fact-project.org/browser/trunk/FACT%2B%2B/src/smartfact.cc#L3131
    dim_network_status = sfc.status().dim
    return dim_network_status == 'Offline'

def is_no_dimctrl_server_available():
    '''no dimctrl server available'''
    # Didn't find a clear way to check this, so I do:
    dim_control_status = sfc.status().dim_control
    return dim_control_status in [
        'Offline',
        'NotReady',
        'ERROR',
        'FATAL',
        ]

def is_no_shift_at_the_moment():
    return not is_shift_at_the_moment

class WindSpeedCheck(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_high_windspeed,
            is_not_parked,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)


class WindGustCheck(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_high_windgusts,
            is_not_parked,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)


class MedianCurrentCheck(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_median_current_high,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)


class MaximumCurrentCheck(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_maximum_current_high,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)


class RelativeCameraTemperatureCheck(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_rel_camera_temperature_high,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)


class BiasNotOperatingDuringDataRun(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_bias_not_operating,
            is_data_run,
            is_data_taking,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)

class BiasChannelsInOverCurrent(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_overcurrent,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)


class BiasVoltageNotAtReference(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_bias_voltage_not_at_reference,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)


class ContainerTooWarm(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_container_too_warm,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)



class DriveInErrorDuringDataRun(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_drive_error,
            is_data_run,
            is_data_taking,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)


class BiasVoltageOnButNotCalibrated(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_voltage_on,
            is_feedback_not_calibrated,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)


class DIMNetworkNotAvailable(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_dim_network_down,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)


class NoDimCtrlServerAvailable(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_no_dimctrl_server_available,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)




class TriggerRateLowForTenMinutes(IntervalCheck, MessageMixin):
    history = pd.DataFrame()

    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_data_taking,
            self.is_trigger_rate_low_for_ten_minutes,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)

    def is_trigger_rate_low_for_ten_minutes(self):
        '''Trigger rate < 1/s for 10 minutes'''
        current_trigger_rate = sfc.trigger_rate().trigger_rate.value
        self._append_to_history(current_trigger_rate)
        self._remove_old_entries()
        df = pd.DataFrame(self.history)
        return not df.empty and (df.rate < 1).all()

    def _append_to_history(self, rate):
        self.history = self.history.append([{'timestamp': datetime.utcnow(), 'rate': rate}])

    def _remove_old_entries(self):
        now = datetime.utcnow()
        self.history = self.history[(now - self.history.timestamp) < timedelta(minutes=10)]


class IsUserAwakeBeforeShutdown(IntervalCheck, MessageMixin):
    '''
    This Check should find out if the user is actually awake some time before
    the scheduled shutdown.

    In order to find out, if the shifter is awake, we need to find out:
      * Is it 20minutes (or less) before shutdown?
      * Who is the current shifter (username)?
      * Is she awake, i.e. did he press the "I am awake button" recently?
    '''
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_20minutes_or_less_before_shutdown,
            is_user_awake,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_SHIFTER)


def is_user_awake():
    awake = {}
    for username, since in fetch_users_awake().items():
        since = pd.to_datetime(since)
        if since > get_next_shutdown() - timedelta(minutes=20):
            awake[username] = since
    if not awake:
        return False
    else:
        return whoisonshift() in awake

def is_20minutes_or_less_before_shutdown():
    '''20min before shutdown'''
    return datetime.utcnow() > get_next_shutdown() - timedelta(minutes=20)


def fetch_users_awake():
    @retry(stop_max_delay=30000,  # 30 seconds max
          wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
          wait_exponential_max=1000,  # but wait 1 second per try maximum
          wrap_exception=True
         )
    def retry_fetch_fail_after_30sec():
        return requests.get('https://ihp-pc41.ethz.ch/iAmAwake').json()

    try:
        return retry_fetch_fail_after_30sec()
    except RetryError:
        return {}

def is_anybody_on_shift():
    '''Nobody on Shift'''
    try:
        whoisonshift()
    except IndexError:
        return False
    else:
        return True


class ShifterOnShift(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            is_shift_at_the_moment,
            is_anybody_on_shift,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_DEVELOPER)


class ParkingChecklistFilled(IntervalCheck, MessageMixin):
    '''
    This Check should find out if the parking/shutdown checklist
    was filled, i.e. "if the shutdown checked by a person"
    within a certain time after the scheduled shutdown.

    This check, does not only run when there is a shift, but
    *after* the shift. So when there is no shift at the moment,
    it is by definition *after* the shift.

    It tries to find out:
     * when the last checklist was filled and
     * when the last shutdown was scheduled.

    If there was no checklist-fill after the last scheduled shutdown it calls.

    Well, if the current time is only up to 10 minutes after the last shutdown,
    we give the human operator a little time to do the actual work.
    '''
    def check(self):
        checklist = [
            is_no_shift_at_the_moment,
            is_last_shutdown_already_10min_past,
            is_checklist_filled,
        ]
        if all(f() for f in checklist):
            return self.message(checklist, category=CATEGORY_DEVELOPER)

def is_last_shutdown_already_10min_past():
    return get_last_shutdown() + timedelta(minutes=10) > datetime.utcnow():


def is_checklist_filled():
    return get_last_parking_checklist_entry() < get_last_shutdown()



