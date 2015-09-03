# -*- encoding:utf-8 -*-
from __future__ import print_function, absolute_import
from collections import defaultdict
import time 
import random
import numpy as np
from datetime import datetime
from pytz import UTC
import requests
from . import Check

class WebDimCheck(Check):
    base_url = "http://fact-project.org/smartfact/data"
    status_page_url = base_url + "/status.data"
    main_page_url = base_url + "/fact.data"
    weather_page_url = base_url + "/weather.data"
    bias_current_page_url = base_url + "/current.data"
    fsc_page_url = base_url + "/fsc.data"

    connection_error_counter = defaultdict(int)


    def _requests_get(self, url):
        while True:
            try:
                r = requests.get(url, timeout=5.)
            except requests.exceptions.ConnectionError:
                self.connection_error_counter[url] += 1
                if self.connection_error_counter[url] >= 10:
                    raise
                else:
                    # sleep between 1 and 2 seconds.
                    time.sleep(1. + random.random())
            else:
                self.connection_error_counter[url]=0
                return r

    
    def _request_page(self):
        self.status_page = self._requests_get(self.status_page_url)
        self.main_page = self._requests_get(self.main_page_url)
        self.weather_page = self._requests_get(self.weather_page_url)
        self.bias_current_page = self._requests_get(self.bias_current_page_url)
        self.fsc_page = self._requests_get(self.fsc_page_url)

    def _fetch_string(self, payload, line, col):
        return payload[line].split()[col]


    def _fetch_float(self, payload, line, col):
        return float(payload[line].split()[col])


    def _parse_payload(self):
        """ Example payload

            ----------------- status_page: ------------------
            1441151157594   1441150920149   losticks    0   1
            #f0fff0 V20r13
            #f0fff0 1:Running[3] [smueller:4950]
            #f0fff0 TakingData
            #f0fff0 Logging
            #f0fff0 OnTrack
            #f0fff0 Valid
            #f0fff0 RunInProgress
            #f0fff0 TriggerOn
            #f0fff0 VoltageOn
            #f0fff0 InProgress
            #f0fff0 InProgress
            #f0fff0 Connected
            #f0fff0 Locked
            #f0fff0 Valid
            #f0fff0 VoltageOn
            #f0fff0 VoltageOn
            #f0fff0 VoltageOn
            #f0fff0 SystemOn
            #f0fff0 Open
            #f0fff0 Connected
            #f0fff0 Valid
            #f0fff0 Valid
            #f0fff0 Valid
            #f0fff0 Valid
            #f0fff0 Ready
            #ffffff &mdash;
            #f0fff0 7 TB
            #f0fff0 552:59:44

            ----------------- main_page: -----------------
            1440764736901   1440741010798   ding    0   0
            #ffffff Idle [single-pe]
            #ffffff  &#9788; [07:35&darr;] &otimes;
            #f0fff0 8.54
            #f0fff0 22.4    20
            #ffffff
            #ffffff

            ----------------- weather_page: --------------
            1440771387000
            #fff8f0 day time [06:44&darr;]
            #ffffff 98% [04:21&uarr;]
            #ffffff 18
            #ffffff -1.7
            #ffffff 26.1
            #ffffff 787
            #ffffff 10.5
            #ffffff 13.1
            #ffffff NNW
            #ffffff 4.51    14:08

            ----------------- bias_current_page: ----------
            1440740960572
            #f0fff0 yes
            #f0fff0 -18.1
            #f0fff0 -4.94
            #f0fff0 -4.95
            #f0fff0 6.23
            #ffffff 0W [0mW]
        """
        self.status_page_payload = self.status_page.content.split('\n')
        self.main_page_payload = self.main_page.content.split('\n')
        self.weather_page_payload = self.weather_page.content.split('\n')
        self.bias_current_page_payload = self.bias_current_page.content.split('\n')
        self.fsc_page_payload = self.fsc_page.content.split('\n')

        self.humidity_outside = self._fetch_float(
            self.weather_page_payload, 5, 1)            
        self.wind_speed = self._fetch_float(
            self.weather_page_payload, 7, 1)
        self.wind_gusts = self._fetch_float(
            self.weather_page_payload, 8, 1)
        

        self.dimctrl_state = self._fetch_string(
            self.main_page_payload, 1, 1)
        self.dimctrl_state = self._fetch_string(
            self.status_page_payload, 2, 1)
        
        self.current_time = datetime.fromtimestamp(
            self._fetch_float(self.main_page_payload, 0, 0) / 1000., 
            UTC)
        self.last_update_time = datetime.fromtimestamp(
            self._fetch_float(self.main_page_payload, 0, 1) / 1000., 
            UTC)

        self.currents_median = self._fetch_float(
            self.bias_current_page_payload, 3, 1)
        self.currents_max = self._fetch_float(
            self.bias_current_page_payload, 5, 1)

        self.rel_cam_temp = self._fetch_float(
            self.main_page_payload, 3, 1)

        self.rel_cam_hum = self._fetch_float(
            self.fsc_page_payload, 1, 1)


    def _load_data_from_webdim_page(self):
        # TODO: this should be called "check"
        # and be called first by each check-method of a sub-class
        # but I think there is an issue in py2-py3 compatible calling of super...
        self._request_page()
        self._parse_payload()


class MainJsStatusCheck(WebDimCheck):
    
    def check(self):
        self._load_data_from_webdim_page()
        if 'Running' not in self.dimctrl_state:
            mesg = "'Running' not in dimctrl_state\n\t{}"
            self.queue.append(mesg.format(self.dimctrl_state))
            self.update_system_status('Main.js', 'Offline', ' ')
        else:
            self.update_system_status('Main.js', 'Running', ' ')

class WeatherCheck(WebDimCheck):

    def check(self):
        self._load_data_from_webdim_page()

        fmt = '{:2.1f}'
        self.update_system_status('wind speed', fmt.format(self.wind_speed), 'km/h')
        self.update_system_status('wind gusts', fmt.format(self.wind_gusts), 'km/h')
        self.update_system_status('humidity', fmt.format(self.humidity_outside), '%')

        if self.humidity_outside >= 98:
            mesg = "humidity_outside >= 98 %: {:2.1f} %"
            self.queue.append(mesg.format(self.humidity_outside))
        if self.wind_speed >= 50:
            mesg = "wind_speed >= 50 km/h: {:2.1f} km/h"
            self.queue.append(mesg.format(self.wind_speed))
        if self.wind_gusts >= 50:
            mesg = "wind_gusts >= 50 km/h: {:2.1f} km/h"
            self.queue.append(mesg.format(self.wind_gusts))

class CurrentCheck(WebDimCheck):

    def check(self):
        self._load_data_from_webdim_page()
        self.update_system_status(
            'bias current median', 
            '{:2.0f}'.format(self.currents_median), 
            u'uA'
        )
        self.update_system_status(
            'bias current max', 
            '{:2.0f}'.format(self.currents_max), 
            u'uA'
        )

        if self.currents_median >= 90:
            mesg = u"median current >= 90 uA {:2.1f} uA"
            self.queue.append(mesg.format(self.currents_median))
        if self.currents_max >= 110:
            mesg = u"maximum current >= 110 uA {:2.1f} uA"
            self.queue.append(mesg.format(self.currents_max))

class RelativeCameraTemperatureCheck(WebDimCheck):

    def check(self):
        self._load_data_from_webdim_page()

        fmt = '{:2.1f}'
        self.update_system_status(
            'rel. camera temp.', fmt.format(self.rel_cam_temp), 'K'
        )

        if self.rel_cam_temp > 10.0:
            mesg = "relative camera temp > 10 K: {:2.1f} %"
            self.queue.append(mesg.format(self.rel_cam_temp))

class RelativeCameraHumidityCheck(WebDimCheck):

    def check(self):
        self._load_data_from_webdim_page()

        fmt = '{:2.1f}'
        self.update_system_status(
            'rel. camera hum.', fmt.format(self.rel_cam_hum), '%'
        )

        if self.rel_cam_hum > 50.0:
            mesg = "relative camera hum. > 50 %: {:2.1f} %"
            self.queue.append(mesg.format(self.rel_cam_hum))