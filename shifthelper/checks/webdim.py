from . import Check, SystemStatusMessage
import smart_fact_crawler
import logging
log = logging.getLogger(__name__)

class MainJsStatusCheck(Check):
    def check(self):
        value = smart_fact_crawler.status()['Dim_Control']
        msg = SystemStatusMessage('Main.js', value, '')
        log.info(msg)
        if 'Running' not in value:
            self.queue.put(msg)

class HumidityCheck(Check):
    def check(self):
        value = smart_fact_crawler.weather()['Humidity_in_Percent']
        msg = SystemStatusMessage('humidity', value, '%')
        log.info(msg)
        if value >= 98:
            self.queue.put(msg)

class WindSpeedCheck(Check):
    def check(self):
        value = smart_fact_crawler.weather()['Wind_speed_in_km_per_h']
        msg = SystemStatusMessage('wind speed', value, 'km/h')
        log.info(msg)
        if value >= 50:
            self.queue.put(msg)

class WindGustCheck(Check):
    def check(self):
        value = smart_fact_crawler.weather()['Wind_gusts_in_km_per_h']
        msg = SystemStatusMessage('wind gusts', value, 'km/h')
        log.info(msg)
        if value >= 50:
            self.queue.put(msg)


class MedianCurrentCheck(Check):
    def check(self):
        value = smart_fact_crawler.currents()['Med_current_per_GAPD_in_uA']
        msg = SystemStatusMessage('median current', value, 'uA')
        log.info(msg)
        if value >= 115:
            self.queue.put(msg)

class MaximumCurrentCheck(Check):
    def check(self):
        value = smart_fact_crawler.currents()['Max_current_per_GAPD_in_uA']
        msg = SystemStatusMessage('maximum current', value, 'uA')
        log.info(msg)
        if value >= 160:
            self.queue.put(msg)

class RelativeCameraTemperatureCheck(Check):
    def check(self):
        value = smart_fact_crawler.main_page()['Rel_camera_temp_in_C']
        msg = SystemStatusMessage('relative camera temp', value, 'K')
        log.info(msg)
        if value >= 15.0:
            self.queue.put(msg)


check_list = [
    MainJsStatusCheck, 
    HumidityCheck, 
    WindSpeedCheck, 
    WindGustCheck, 
    MedianCurrentCheck, 
    MaximumCurrentCheck, 
    RelativeCameraTemperatureCheck
]
