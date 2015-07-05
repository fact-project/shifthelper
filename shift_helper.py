#!/usr/bin/env ipython
# coding: utf-8
from __future__ import print_function
from blessings import Terminal
import sys
import time
import Skype4Py
import fact.dim

term = Terminal()

dns = fact.dim.Dns('newdaq')
servers = dns.servers()
dimctrl = servers['DIM_CONTROL']
weather = servers['MAGIC_WEATHER']

skype = Skype4Py.Skype()
skype.Attach()

phone_ringing_time = 15 # in sec. do not set larger than delay_between_checks.
delay_between_checks = 60 # in sec.

assert phone_ringing_time < delay_between_checks

def CallStatusText(status):
    return skype.Convert.CallStatusToText(status)

def OnCall(call, status):
    """ callback function (is called, whenever the state of the skypecall 
        changes.

        (first if)
        It is basically making sure, that the shift_helper hangs up
        as soon as you or your answering machine or voicebox take the call.
        so the costs of these calls stay as low as possible.

        (second if)
        This makes sure, that the call is ended, after it was ringing 10sec
        (or a little less)
        The reason for this is the following:
        When I drop the call on my cell-phone, the call would actually be 
        diverted to my voicebox. So the connection gets established.
        Then the shift_helpers call is connected to my voicebox. 
        Nobody is saying anything, but the call will still cost money.
        That alone is no problem.
        But after 30sec the shift_helper would again try to place a call ... 
        while another call is still active, which leads to an exception,
        which is not handled at the moment (FIXME)
        
    """
    CallStatus = status
    # print('Call status text: ', CallStatusText(status))
    if status == Skype4Py.clsInProgress:
        call.Finish()
    elif status == Skype4Py.clsEarlyMedia:
        time.sleep(phone_ringing_time)
        call.Finish()
    
skype.OnCallStatus = OnCall


# examples: 
#     my_phone_number = '+123456789'   # calls you on your phone
#     my_phone_number = None           # if you want to be asked for it on the command line
#     my_phone_number = 'dominikneise' # calls you on your skype account
if len(sys.argv) > 1:
    my_phone_number = sys.argv[1]
else:
    my_phone_number = None

calling_worked = False
while (not calling_worked or my_phone_number is None):
    if my_phone_number is None:
        my_phone_number = raw_input('Please enter your phone number like +1234\n')
    my_phone_number = my_phone_number.replace(' ', '')
    print("You entered: ", my_phone_number)
    confirm_correctness = raw_input('Is that number correct? (y/n): ')
    if not confirm_correctness.lower()[0] == 'y':
        my_phone_number = None

    if my_phone_number is not None:
        print("I will try to call you now")
        skype.PlaceCall(my_phone_number)
        recieved_call = raw_input('Did your phone ring? (y/n): ')
        if recieved_call.lower()[0] == 'y':
            calling_worked = True	    

while True:
  try:
    temperature = weather.data()[1]
    humidity_outside = weather.data()[3]
    wind_speed = weather.data()[5]
    wind_gusts = weather.data()[6]
    dimctrl_state = dimctrl.state()[0][:-1]
    print('\n', term.cyan(time.asctime()), ':', sep='')
    print('DimCtrl state:', dimctrl_state)
    print('Humidity: {:2.1f} %'.format(humidity_outside))
    print('Wind (gusts): {:2.1f} ({:1.2f}) km/h'.format(wind_speed, wind_gusts))
    if 'Running' not in dimctrl_state:
      print(term.red("    !!!! 'Running' not in dimctrl_state\n\t"), dimctrl_state)
      skype.PlaceCall(my_phone_number)
    elif humidity_outside >= 98:
      print(term.red("    !!!! humidity_outside >= 98:"), humidity_outside)
      skype.PlaceCall(my_phone_number)
    elif wind_speed >= 50:
      print(term.red("    !!!! wind_speed >= 50:"), wind_speed)
      skype.PlaceCall(my_phone_number)
   # elif wind_gusts >= 40:
   # print(term.red("    !!!! wind_gusts >= 40:"), wind_gusts)
   # skype.PlaceCall(my_phone_number)
    else:
      print(term.green("Everything OK!"))
    time.sleep(delay_between_checks)
  
  except KeyboardInterrupt, SystemExit:
    raise 
  except Exception as e:
    print(e)
    skype.PlaceCall(my_phone_number)
    time.sleep(delay_between_checks)
