from __future__ import print_function
from datetime import datetime
import fact.dim
from blessings import Terminal
term = Terminal()

dimctrl = None
weather = None


def setup():
    dns = fact.dim.Dns('newdaq')
    servers = dns.servers()
    global dimctrl
    global weather
    dimctrl = servers['DIM_CONTROL']
    weather = servers['MAGIC_WEATHER']


def perform_checks():
    temperature = weather.data()[1]
    humidity_outside = weather.data()[3]
    wind_speed = weather.data()[5]
    wind_gusts = weather.data()[6]
    dimctrl_state = dimctrl.state()[0][:-1]
    print('DimCtrl state:', dimctrl_state)
    print('Humidity: {:2.1f} %'.format(humidity_outside))
    print('Wind (gusts): {:2.1f} ({:1.2f}) km/h'.format(
        wind_speed, wind_gusts))
    if 'Running' not in dimctrl_state:
        mesg = term.red("    !!!! 'Running' not in dimctrl_state\n\t{}")
        raise ValueError(mesg.format(dimctrl_state))
    if humidity_outside >= 98:
        mesg = term.red("    !!!! humidity_outside >= 98 %: {:2.1f} %")
        raise ValueError(mesg.format(humidity_outside))
        skype.PlaceCall(my_phone_number)
    if wind_speed >= 50:
        mesg = term.red("    !!!! wind_speed >= 50 km/h: {:2.1f} km/h")
        raise ValueError(mesg.format(wind_speed))
   # elif wind_gusts >= 40:
   #   mesg = term.red("    !!!! wind_gusts >= 40 km/h: {:2.1f}")
   #   raise ValueError(mesg.format(wind_gusts))
