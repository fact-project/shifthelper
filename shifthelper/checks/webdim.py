# -*- encoding:utf-8 -*-
from __future__ import print_function, absolute_import
from . import Check

import smart_fact_crawler as sfc


class MainJsStatusCheck(Check):

    def check(self):
        state = sfc.status().dim_control
        if 'Running' not in state:
            mesg = "'Running' not in dimctrl_state: {!r}"
            self.queue.append(mesg.format(state))
        self.update_system_status('Main.js', state, ' ')


class WeatherCheck(Check):

    def check(self):
        w = sfc.weather()
        wind_speed = w.wind_speed.value
        wind_gusts = w.wind_gusts.value
        humidity = w.humidity.value

        fmt = '{:2.1f}'
        self.update_system_status(
            'wind speed', fmt.format(wind_speed), w.wind_speed.unit
        )
        self.update_system_status(
            'wind gusts', fmt.format(wind_gusts), w.wind_gusts.unit
        )
        self.update_system_status(
            'humidity', fmt.format(humidity), w.humidity.unit
        )

        if humidity >= 98:
            mesg = "humidity_outside >= 98 %: {:2.1f} "+w.humidity.unit
            self.queue.append(mesg.format(humidity))
        if wind_speed >= 50:
            mesg = "wind_speed >= 50 km/h: {:2.1f} "+w.wind_speed.unit
            self.queue.append(mesg.format(wind_speed))
        if wind_gusts >= 50:
            mesg = "wind_gusts >= 50 km/h: {:2.1f} "+w.wind_gusts.unit
            self.queue.append(mesg.format(wind_gusts))


class CurrentCheck(Check):

    def check(self):
        c = sfc.currents()

        if c.calibrated:
            median_current = c.median_per_sipm.value
            max_current = c.max_per_sipm.value

            if median_current >= 115:
                mesg = u"median current >= 115 uA {:2.1f} "
                mesg+= c.median_per_sipm.unit
                self.queue.append(mesg.format(median_current))
            if max_current >= 160:
                mesg = u"maximum current >= 160 uA {:2.1f} "
                mesg+= c.max_per_sipm.unit
                self.queue.append(mesg.format(max_current))
        else:
            median_current = float('nan')
            max_current = float('nan')

        self.update_system_status(
            'bias current median',
            '{:2.0f}'.format(median_current), c.median_per_sipm.unit
        )
        self.update_system_status(
            'bias current max',
            '{:2.0f}'.format(max_current), c.max_per_sipm.unit
        )

class RelativeCameraTemperatureCheck(Check):

    def check(self):
        main_page = sfc.main_page()

        fmt = '{:2.1f}'
        self.update_system_status(
            'rel. camera temp.',
            fmt.format(main_page.relative_camera_temperature.value),
            main_page.relative_camera_temperature.unit
        )

        if main_page.relative_camera_temperature.value > 15.0:
            mesg = "relative camera temp > 15 K: {:2.1f} "
            mesg+= main_page.relative_camera_temperature.unit
            self.queue.append(
                mesg.format(main_page.relative_camera_temperature.value))
