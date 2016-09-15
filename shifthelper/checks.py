from custos import IntervalCheck
import smart_fact_crawler as sfc
from .tools.is_shift import is_shift_at_the_moment
import requests
from abc import ABCMeta, abstractmethod

import pandas as pd
import datetime
from datetime import timedelta, datetime
import numpy as np
import re

class FactIntervalCheck(IntervalCheck, metaclass=ABCMeta):

    def check(self):
        if is_shift_at_the_moment():
            text = self.inner_check()
            if text is not None:
                if self.all_recent_alerts_acknowledged():
                    self.info(text)
                else:
                    self.warning(text)


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
        if 'Running' not in sfc.status()['Dim_Control']:
            return 'Main.js is not running'


class HumidityCheck(FactIntervalCheck):
    def inner_check(self):
        lid_status = sfc.status()['Lid_control']
        # this translation is a dirty hack,
        # and not guaranteed to work.
        lid_status_translation = {
            'Inconsistent': 'Closed',
            'Closed': 'Closed',
            'Open': 'Open',
            'PowerProblem': 'Open'
        }
        lid_status = lid_status_translation.get(lid_status, 'Unknown')

        humidity = sfc.weather()['Humidity_in_Percent']
        if humidity >= 98 and lid_status=='Open':
            return 'Humidity > 98% while Lid open'


def is_parked():
    pointing = sfc.drive()['pointing']
    az = pointing['Azimuth_in_Deg']
    zd = pointing['Zenith_Distance_in_Deg']
    is_locked = sfc.status()['Drive_control'] == 'Locked'
    # should is_locked be taken into account here?
    # pointing north is enough ...
    # but driving through north ... is not :-|
    return (-5 < az < 5) and (90 < zd < 180)

def is_drive_error():
    drive_state = sfc.status()['Drive_control']
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
    return sfc.status()['MCP'] in ['TaTakingDatakingData', 'TriggerOn']

def is_data_run():
    # fMcpConfigurationName=='data' || fMcpConfigurationName=='data-rt';
    # this fMcpConfigurationName seems to turn um in square brackets []
    # inside sfc.main_page()['System_Status'], but I'm not sure yet.
    # yes it does: example: 
    # sfc.main_page()['System_Status'] --> 'Idle [single-pe]'
    try:
        config_name = re.search('\[(.*)\]', sfc.main_page()['System_Status']).groups()[0]
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
    bias_state = sfc.status()['Bias_control']
    return bias_state in [
        'Offline',
        'NotReady',
        'Ready',
        'Disconnected',
        'Connecting',
        'Initializing',
        'Connected',
    ]

class WindSpeedCheck(FactIntervalCheck):
    def inner_check(self):
        if sfc.weather()['Wind_speed_in_km_per_h'] >= 50 and not is_parked:
            'Wind speed > 50 km/h and not parked'

class WindGustCheck(FactIntervalCheck):
    def inner_check(self):
        if sfc.weather()['Wind_gusts_in_km_per_h'] >= 50 and not is_parked:
            return 'Wind gusts > 50 km/h and not parked'

class MedianCurrentCheck(FactIntervalCheck):
    def inner_check(self):
        if sfc.currents()['Med_current_per_GAPD_in_uA'] >= 115:
            return 'Median GAPD current > 115uA'

class MaximumCurrentCheck(FactIntervalCheck):
    def inner_check(self):
        if sfc.currents()['Max_current_per_GAPD_in_uA'] >= 160:
            return 'Maximum GAPD current > 160uA'

class RelativeCameraTemperatureCheck(FactIntervalCheck):
    def inner_check(self):
        if sfc.main_page()['Rel_camera_temp_in_C'] >= 15.0:
            return 'relative camera temperature > 15°C'


class BiasNotOperatingDuringDataRun(FactIntervalCheck):
    def inner_check(self):
        if (is_bias_not_operating()
                and is_data_taking()
                and is_data_run()):
            return 'Bias not operating during data run'


class BiasChannelsInOverCurrent(FactIntervalCheck):
    def inner_check(self):
        bias_state = sfc.status()['Bias_control']
        if bias_state == 'OverCurrent':
            return 'Bias Channels in Over Current'


class BiasVoltageNotAtReference(FactIntervalCheck):
    def inner_check(self):
        bias_state = sfc.status()['Bias_control']
        if bias_state == 'NotReferenced':
            return 'Bias Voltage not at reference.'


class ContainerTooWarm(FactIntervalCheck):
    def inner_check(self):
        if sfc.container_temperature()['Current_temperature_in_C'] > 42:
            return 'Container Temperature above 42 deg C'


class DriveInErrorDuringDataRun(FactIntervalCheck):
    def inner_check(self):
        if (is_drive_error()
                and is_data_taking()
                and is_data_run()):
            return 'Drive in Error during Data run'
