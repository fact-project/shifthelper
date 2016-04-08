# -*- encoding:utf-8 -*-
from __future__ import print_function, absolute_import
from . import Check

import smart_fact_crawler


class MainJsStatusCheck(Check):

    def check(self):
        s = smart_fact_crawler.status()
        state = s['Dim_Control'][0]
        if 'Running' not in state:
            mesg = "'Running' not in dimctrl_state: {!r}"
            self.queue.append(mesg.format(state))
        self.update_system_status('Main.js', state, ' ')


class WeatherCheck(Check):

    def check(self):
        w = smart_fact_crawler.weather()

        fmt = '{:2.1f}'
        self.update_system_status(
            'wind speed', fmt.format(w['Wind_speed_in_km_per_h']), 'km/h'
        )
        self.update_system_status(
            'wind gusts', fmt.format(w['Wind_gusts_in_km_per_h']), 'km/h'
        )
        self.update_system_status(
            'humidity', fmt.format(w['Humidity_in_Percent']), '%'
        )

        if w['Humidity_in_Percent'] >= 98:
            mesg = "humidity_outside >= 98 %: {:2.1f} %"
            self.queue.append(mesg.format(w['Humidity_in_Percent']))
        if w['Wind_speed_in_km_per_h'] >= 50:
            mesg = "wind_speed >= 50 km/h: {:2.1f} km/h"
            self.queue.append(mesg.format(w['Wind_speed_in_km_per_h']))
        if w['Wind_gusts_in_km_per_h'] >= 50:
            mesg = "wind_gusts >= 50 km/h: {:2.1f} km/h"
            self.queue.append(mesg.format(w['Wind_gusts_in_km_per_h']))


class CurrentCheck(Check):

    def check(self):
        c = smart_fact_crawler.currents()

        self.update_system_status(
            'bias current median',
            '{:2.0f}'.format(c['Med_current_per_GAPD_in_uA']),
            u'uA'
        )
        self.update_system_status(
            'bias current max',
            '{:2.0f}'.format(c['Max_current_per_GAPD_in_uA']),
            u'uA'
        )

        if c['Med_current_per_GAPD_in_uA'] >= 90:
            mesg = u"median current >= 90 uA {:2.1f} uA"
            self.queue.append(mesg.format(c['Med_current_per_GAPD_in_uA']))
        if c['Max_current_per_GAPD_in_uA'] >= 110:
            mesg = u"maximum current >= 110 uA {:2.1f} uA"
            self.queue.append(mesg.format(c['Max_current_per_GAPD_in_uA']))


class RelativeCameraTemperatureCheck(Check):

    def check(self):
        main_page = smart_fact_crawler.main_page()

        fmt = '{:2.1f}'
        self.update_system_status(
            'rel. camera temp.',
            fmt.format(main_page['Rel_camera_temp_in_C']),
            'K'
        )

        if main_page['Rel_camera_temp_in_C'] > 10.0:
            mesg = "relative camera temp > 10 K: {:2.1f} K"
            self.queue.append(mesg.format(main_page['Rel_camera_temp_in_C']))
