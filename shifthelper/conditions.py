''' conditions are boolean functions, testing for one particular condition.

condition fuctions __doc__ is used for human readable message generation.
So keep them one-liners please.


conditions are used by the Check-classes inside checks.py
'''
import re as regex
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
import logging

from .tools.is_shift import (
    is_shift_at_the_moment,
    get_next_shutdown,
    get_last_shutdown,
)
from .tools.shift import get_current_shifter
from .tools import get_last_parking_checklist_entry
from .tools import fetch_users_awake
from .tools import fetch_dummy_alerts
from . import tools
from . import retry_smart_fact_crawler as sfc
from .debug_log_wrapper import log_call_and_result


log = logging.getLogger(__name__)
UTC = timezone.utc


def is_older(timestamp, delta):
    ''' Test if a timestamp is older than a certain amount of time'''
    return (datetime.now(tz=UTC) - timestamp) > delta


@log_call_and_result
def is_mainjs_not_running():
    '''Main.js is not running'''
    dim_control_status = sfc.status().dim_control
    return 'Running' not in dim_control_status


@log_call_and_result
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


@log_call_and_result
def is_humidity_high():
    '''Humidity > 98%'''
    return sfc.weather().humidity.value >= 98


@log_call_and_result
def is_not_parked():
    ''' Telescope not parked '''
    az = sfc.drive_pointing().azimuth.value
    zd = sfc.drive_pointing().zenith_distance.value
    # is_locked = sfc.status().drive_control == 'Locked'
    # should is_locked be taken into account here?
    # pointing north is enough ...
    # but driving through north ... is not :-|
    return not ((-5 < az < 5) and (90 < zd))


@log_call_and_result
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


@log_call_and_result
def is_data_taking():
    '''is taking data'''
    # if MCP::State::kTriggerOn ||MCP::State::kTakingData;
    # the state name strings, I took from dimctrl on newdaq, typing `st`
    return sfc.status().mcp in ['TakingData', 'TriggerOn']


@log_call_and_result
def is_data_run():
    '''is doing physics data run'''
    # fMcpConfigurationName=='data' || fMcpConfigurationName=='data-rt';
    # this fMcpConfigurationName seems to turn um in square brackets []
    # inside sfc.main_page().system_status, but I'm not sure yet.
    # yes it does: example:
    # sfc.main_page().system_status --> 'Idle [single-pe]'
    result = sfc.main_page().system_status
    if result is None:
        return False
    search_result = regex.search(
        r'\[(.*)\]',
        result,
    )
    if search_result is None:
        # regex did not match
        return False
    else:
        config_name = search_result.groups()[0]
        return config_name in ['data', 'data-rt']


@log_call_and_result
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


@log_call_and_result
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


@log_call_and_result
def is_high_windspeed():
    '''Wind speed > 50 km/h'''
    magic_weather = sfc.weather(fallback=True)
    max_age = timedelta(minutes=10)
    timestamp = magic_weather.timestamp

    if magic_weather.timestamp is not None and not is_older(timestamp, max_age):
        wind_speed = magic_weather.wind_speed.value
        return np.isnan(wind_speed) or wind_speed >= 50
    else:
        log.warning('MAGIC weather outdated, using TNG weather info')
        tng_weather = sfc.tng_weather()
        return tng_weather.wind_speed.value >= 50


@log_call_and_result
def is_weather_outdatet():
    ''' MAGIC and TNG weather not updated in the last 10 minutes '''
    magic_weather = sfc.weather(fallback=True)
    max_age = timedelta(minutes=10)
    timestamp = magic_weather.timestamp

    if magic_weather.timestamp is not None and not is_older(timestamp, max_age):
        return False
    else:
        log.warning('MAGIC Weather outdated, falling back to TNG')
        tng_weather = sfc.tng_weather()
        return is_older(tng_weather.timestamp, max_age)


@log_call_and_result
def is_smartfact_outdatet():
    ''' SMARTFACT not updated in the last 10 minutes '''
    timestamp = sfc.main_page().timestamp_1
    if timestamp is None:
        raise ValueError('Could not get smartfact timestamp')
    return is_older(timestamp, timedelta(minutes=10))


@log_call_and_result
def is_high_windgusts():
    '''Wind gusts > 50 km/h or MAGIC weather not available and TNG wind > 50 km/h'''
    magic_weather = sfc.weather(fallback=True)
    max_age = timedelta(minutes=10)
    timestamp = magic_weather.timestamp

    if magic_weather.timestamp is not None and not is_older(timestamp, max_age):
        wind_gusts = magic_weather.wind_gusts.value
        return np.isnan(wind_gusts) or wind_gusts >= 50
    else:
        log.warning('MAGIC weather outdated, using TNG weather info')
        tng_weather = sfc.tng_weather()
        return tng_weather.wind_speed.value >= 50


@log_call_and_result
def is_median_current_high():
    '''Median GAPD current > 115uA'''
    current_info = sfc.sipm_currents()
    is_currents_calibrated = current_info.calibrated
    median_current = current_info.median_per_sipm.value
    return is_currents_calibrated and median_current >= 115


@log_call_and_result
def is_maximum_current_high():
    '''Maximum GAPD current > 160uA'''
    current_info = sfc.sipm_currents()
    is_currents_calibrated = current_info.calibrated
    max_current = current_info.max_per_sipm.value
    return is_currents_calibrated and max_current >= 160


@log_call_and_result
def is_rel_camera_temperature_high():
    '''relative camera temperature > 15°C'''
    relative_temperature = sfc.main_page().relative_camera_temperature.value
    if np.isnan(relative_temperature):
        raise ValueError('Could not get relative camera temperature')
    return relative_temperature >= 15.0


@log_call_and_result
def is_overcurrent():
    '''Bias Channels in Over Current'''
    return sfc.status().bias_control == 'OverCurrent'


@log_call_and_result
def is_bias_voltage_not_at_reference():
    '''Bias Voltage not at reference'''
    return sfc.status().bias_control == 'NotReferenced'


@log_call_and_result
def is_container_too_warm():
    '''Container Temperature above 42 °C'''
    container_temperature = float(sfc.container_temperature().current.value)
    return container_temperature > 42


@log_call_and_result
def is_voltage_on():
    '''Bias Voltage is On'''
    median_voltage = sfc.sipm_voltages().median.value
    return sfc.status().bias_control == 'VoltageOn' and median_voltage > 3


@log_call_and_result
def is_dim_network_down():
    '''DIM network not available'''
    # can be checked this way according to:
    # https://trac.fact-project.org/browser/trunk/FACT%2B%2B/src/smartfact.cc#L3131
    dim_network_status = sfc.status().dim
    return dim_network_status == 'Offline'


@log_call_and_result
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


@log_call_and_result
def is_no_shift_at_the_moment():
    '''no shift at the moment'''
    return not is_shift_at_the_moment()


@log_call_and_result
def is_nobody_ready_for_shutdown():
    '''Nobody is ready for shutdown'''
    ready_for_shutdown = {}
    for username, since in fetch_users_awake().items():
        since = pd.to_datetime(since)
        if since > get_next_shutdown() - timedelta(minutes=30):
            ready_for_shutdown[username] = since
    return not ready_for_shutdown


@log_call_and_result
def update_heartbeat():
    '''HeartbeatMonitor not ok'''
    log = logging.getLogger(__name__)
    heartbeats = tools.update_heartbeat()
    if "heartbeatMonitor" not in heartbeats:
        log.debug("HeartbeatMonitor offline?")
        return True
    else:
        timestamp = pd.to_datetime(heartbeats['heartbeatMonitor'])
        if is_older(timestamp, timedelta(minutes=10)):
            log.debug('heartbeat_monitor_age > timedelta(minutes=10)')
            return True
    return False


@log_call_and_result
def is_dummy_alert_by_shifter():
    '''Dummy Alert'''
    log = logging.getLogger(__name__)
    for username, since in fetch_dummy_alerts().items():
        since = pd.to_datetime(since)

        if not is_older(since, timedelta(minutes=3)):
            log.debug('%s issued a dummy alert at: %s', username, since)
            try:
                current_shifter = get_current_shifter().username
            except IndexError:
                log.debug('Nobody on shift')
                return False
            log.debug('current shifter is: %s', current_shifter)
            if current_shifter != username:
                log.debug('no message sent')
                return False
            else:
                log.debug('sending dummy alert message')
                return True


@log_call_and_result
def is_20minutes_or_less_before_shutdown():
    '''20min before shutdown'''
    return (get_next_shutdown() - datetime.now(tz=UTC)) < timedelta(minutes=20)


@log_call_and_result
def is_nobody_on_shift():
    '''Nobody on Shift'''
    try:
        get_current_shifter()
    except IndexError:
        return True
    else:
        return False


@log_call_and_result
def is_last_shutdown_already_10min_past():
    '''Last Shutdown is already 10min past'''
    return is_older(get_last_shutdown(), timedelta(minutes=10))


@log_call_and_result
def is_checklist_not_filled():
    '''checklist not filled'''
    return get_last_parking_checklist_entry() < get_last_shutdown()


@log_call_and_result
def is_trigger_rate_low_for_ten_minutes():
    '''Trigger rate < 1/s for 10 minutes'''
    self = is_trigger_rate_low_for_ten_minutes

    if not hasattr(self, 'history'):
        self.history = pd.DataFrame()

    current_trigger_rate = sfc.trigger_rate().trigger_rate.value
    self.history = self.history.append(
        [{
            'timestamp': datetime.now(tz=UTC),
            'rate': current_trigger_rate,
        }]
    )
    now = datetime.now(tz=UTC)
    self.history = self.history[
        (now - self.history.timestamp) < timedelta(minutes=10)
    ]
    df = pd.DataFrame(self.history)
    return not df.empty and (df.rate < 1).all()
