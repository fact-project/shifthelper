''' conditions are boolean functions, testing for one particular condition.

condition fuctions __doc__ is used for human readable message generation.
So keep them one-liners please.


conditions are used by the Check-classes inside checks.py
'''
import re as regex
from datetime import datetime, timedelta
from pandas import to_datetime

from .tools.is_shift import is_shift_at_the_moment, get_next_shutdown, get_last_shutdown
from .tools.whosonshift import whoisonshift
from .tools import get_last_parking_checklist_entry
from .tools import fetch_users_awake
from . import retry_smart_fact_crawler as sfc
from .tools import qla


def is_mainjs_not_running():
    '''Main.js is not running'''
    dim_control_status = sfc.status().dim_control
    return 'Running' not in dim_control_status

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
        config_name = regex.search(
            r'\[(.*)\]',
            sfc.main_page().system_status
            ).groups()[0]
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


def is_nobody_awake():
    '''Parker not Awake'''
    awake = {}
    for username, since in fetch_users_awake().items():
        since = to_datetime(since)
        if since > get_next_shutdown() - timedelta(minutes=20):
            awake[username] = since
    if not awake:
        return True
    else:
        return whoisonshift() not in awake

def is_20minutes_or_less_before_shutdown():
    '''20min before shutdown'''
    return datetime.utcnow() > get_next_shutdown() - timedelta(minutes=20)


def is_nobody_on_shift():
    '''Nobody on Shift'''
    try:
        whoisonshift()
    except IndexError:
        return True
    else:
        return False

def is_last_shutdown_already_10min_past():
    '''Last Shutdown is already 10min past'''
    return get_last_shutdown() + timedelta(minutes=10) > datetime.utcnow()


def is_checklist_not_filled():
    '''checklist not filled'''
    return get_last_parking_checklist_entry() > get_last_shutdown()



def is_significant_flare_detected():
    '''A Flare was detected'''
    data = qla.get_data()
    if data is None:
        return False
    if len(data.index) == 0:
        return False



    significance_cut = 3 # sigma
    significant = data[data.significance >= significance_cut]

    qla_max_rates = data.groupby('fSourceName').agg({
        'rate': 'max',
        'fSourceKEY': 'median',
    })
    for source, data in qla_max_rates.iterrows():
        rate = float(data['rate'])

        significant_qla_max_rates = significant.groupby('fSourceName').agg({
            'rate': 'max',
            'fSourceKEY': 'median',
        })

        for source, data in significant_qla_max_rates.iterrows():
            if float(data['rate']) > qla.create_alert_rate()[source]:
                return True

