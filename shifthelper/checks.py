from custos import IntervalCheck
import smart_fact_crawler
from .tools.is_shift import is_shift_at_the_moment

class MainJsStatusCheck(IntervalCheck):
    def check(self):
        if is_shift_at_the_moment():
            value = smart_fact_crawler.status()['Dim_Control']
            if 'Running' not in value:
                self.warning("Main.js is not running")

class HumidityCheck(IntervalCheck):
    def check(self):
        if is_shift_at_the_moment():
            value = smart_fact_crawler.weather()['Humidity_in_Percent']
            if value >= 98:
                self.warning("Humidity > 98%")


class WindSpeedCheck(IntervalCheck):
    def check(self):
        if is_shift_at_the_moment():
            value = smart_fact_crawler.weather()['Wind_speed_in_km_per_h']
            if value >= 50:
                self.warning("Wind speed > 50 km/h")

class WindGustCheck(IntervalCheck):
    def check(self):
        if is_shift_at_the_moment():
            value = smart_fact_crawler.weather()['Wind_gusts_in_km_per_h']
            if value >= 50:
                self.warning("Wind gusts > 50 km/h")

class MedianCurrentCheck(IntervalCheck):
    def check(self):
        if is_shift_at_the_moment():
            value = smart_fact_crawler.currents()['Med_current_per_GAPD_in_uA']
            if value >= 115:
                self.info("Median GAPD current > 115uA")

class MaximumCurrentCheck(IntervalCheck):
    def check(self):
        if is_shift_at_the_moment():
            value = smart_fact_crawler.currents()['Max_current_per_GAPD_in_uA']
            if value >= 160:
                self.info("Maximum GAPD current > 160uA")

class RelativeCameraTemperatureCheck(IntervalCheck):
    def check(self):
        if is_shift_at_the_moment():
            value = smart_fact_crawler.main_page()['Rel_camera_temp_in_C']
            if value >= 15.0:
                self.info("relative camera temperature > 15°C")
