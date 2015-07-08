# -*- encoding:utf-8 -*-
from __future__ import print_function
import numpy as np
import fact.dim
from blessings import Terminal
from fact_exceptions import SecurityException, DataTakingException
term = Terminal()

dimctrl = None
weather = None
feedback = None

crazy_patches = [66, 191, 193]


def setup(args):
    dns = fact.dim.Dns('newdaq')
    servers = dns.servers()
    global dimctrl
    dimctrl = servers['DIM_CONTROL']

    global weather
    weather = servers['MAGIC_WEATHER']
    global feedback
    feedback = servers['FEEDBACK']


def perform_checks():
    humidity_outside = weather.data()[3]
    wind_speed = weather.data()[5]
    wind_gusts = weather.data()[6]
    dimctrl_state = dimctrl.state()[0][:-1]

    # get the currents, leave out patches with crazy pixels
    currents = np.array(feedback.calibrated_currents()[:320])
    # TB does not exclude the crazy channels, so we also don't do it for now.
    # currents[crazy_patches] = 0
    median = np.median(currents)
    max_current = currents.max()

    print('DimCtrl state:', dimctrl_state)
    print('Humidity: {:2.1f} %'.format(humidity_outside))
    print('Wind (gusts): {:2.1f} ({:1.2f}) km/h'.format(
        wind_speed, wind_gusts))
    print(u'Currents (med/max): {: 2.2f} μA / {: 2.2f} μA'.format(
        median, max_current))

    if 'Running' not in dimctrl_state:
        mesg = term.red("    !!!! 'Running' not in dimctrl_state\n\t{}")
        raise DataTakingException(mesg.format(dimctrl_state))
    if humidity_outside >= 98:
        mesg = term.red("    !!!! humidity_outside >= 98 %: {:2.1f} %")
        raise SecurityException(mesg.format(humidity_outside))
    if wind_speed >= 50:
        mesg = term.red("    !!!! wind_speed >= 50 km/h: {:2.1f} km/h")
        raise SecurityException(mesg.format(wind_speed))
    if median >= 90:
        mesg = term.red(u"    !!!! median current >= 90 μA {:2.1f} μA")
        raise SecurityException(mesg.format(median))
    if max_current >= 110:
        mesg = term.red(u"    !!!! maximum current >= 110 μA {:2.1f} μA")
        raise SecurityException(mesg.format(max_current))
