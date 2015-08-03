# -*- encoding:utf-8 -*-
from __future__ import print_function, absolute_import
import numpy as np
import fact.dim

from . import Check

dns = fact.dim.Dns('newdaq')
servers = dns.servers()

class MainJsStatusCheck(Check):
    dimctrl = servers['DIM_CONTROL']

    def check(self):
        dimctrl_state = self.dimctrl.state()[0][:-1]
        if 'Running' not in dimctrl_state:
            mesg = "'Running' not in dimctrl_state\n\t{}"
            self.queue.append(mesg.format(dimctrl_state))


class WeatherCheck(Check):
    weather = servers['MAGIC_WEATHER']

    def check(self):
        humidity_outside = self.weather.data()[3]
        wind_speed = self.weather.data()[5]
        wind_gusts = self.weather.data()[6]
        if humidity_outside >= 98:
            mesg = "humidity_outside >= 98 %: {:2.1f} %"
            self.queue.append(mesg.format(humidity_outside))
        if wind_speed >= 50:
            mesg = "wind_speed >= 50 km/h: {:2.1f} km/h"
            self.queue.append(mesg.format(wind_speed))
        if wind_gusts >= 50:
            mesg = "wind_gusts >= 50 km/h: {:2.1f} km/h"
            self.queue.append(mesg.format(wind_gusts))


class CurrentCheck(Check):
    feedback = servers['FEEDBACK']
    crazy_patches = [66, 191, 193]

    def check(self):
        currents = np.array(self.feedback.calibrated_currents()[:320])
        # In the DataTaking limits it is stated, that crazy pixels are excluded
        # from these limits but TB does not exclude the crazy channels,
        # so we also don't do it for now.

        # currents[self.crazy_patches] = 0
        currents_median = np.median(currents)
        currents_max = currents.max()
        if currents_median >= 90:
            mesg = u"median current >= 90 μA {:2.1f} μA"
            self.queue.append(mesg.format(currents_median))
        if currents_max >= 110:
            mesg = u"maximum current >= 110 μA {:2.1f} μA"
            self.queue.append(mesg.format(currents_max))