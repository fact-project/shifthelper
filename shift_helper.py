#!/usr/bin/env ipython
# coding: utf-8
from __future__ import print_function
from blessings import Terminal
import sys
import time
import Skype4Py
import fact.dim
from collections import defaultdict
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine

phone_ringing_time = 15 # in sec. do not set larger than delay_between_checks.
delay_between_checks = 60 # in sec.

assert phone_ringing_time < delay_between_checks

# get the correct night in fact format, if it is after 0:00, take the date
# of yesterday
timestamp = datetime.utcnow()
if timestamp.hour < 8:
    timestamp = timestamp - timedelta(days=1)
night = int(timestamp.strftime('%Y%m%d'))

term = Terminal()

dns = fact.dim.Dns('newdaq')
servers = dns.servers()
dimctrl = servers['DIM_CONTROL']
weather = servers['MAGIC_WEATHER']
factdb = create_engine("mysql+mysqldb://<databasecredentials>")

max_rate = defaultdict(lambda : 0)
alert_rate= defaultdict(lambda : 10)
alert_rate['Mrk 501'] = 45
alert_rate['Mrk 421'] = 45
keys = [
    'QLA.fRunID',
    'QLA.fNight',
    'QLA.fNumExcEvts',
    'QLA.fOnTimeAfterCuts',
    'RunInfo.fRunStart',
    'Source.fSourceName',
]
sql_query = 'SELECT ' + ', '.join(keys) + '\n' 
sql_query += 'FROM AnalysisResultsRunLP QLA\n'
sql_query += 'LEFT JOIN RunInfo \n'
sql_query += 'ON QLA.fRunID = RunInfo.fRunID AND QLA.fNight = RunInfo.fNight \n'
sql_query += 'LEFT JOIN Source \n'
sql_query += 'ON RunInfo.fSourceKEY = Source.fSourceKEY \n'
sql_query += 'WHERE QLA.fNight = {:d} '.format(night)

def get_max_rates():
    ''' this will get the QLA results to call if you have to send an alert '''
    data = pd.read_sql_query(sql_query, factdb, parse_dates=['fRunStart'])
    # if no qla data is available, return None
    data = data.dropna()
    if len(data.index) == 0:
        return None
    data.set_index('fRunStart', inplace=True)
    grouped = data.groupby('fSourceName')
    binned = grouped.resample(
        '20Min',
        how={'fNumExcEvts':'sum', 'fOnTimeAfterCuts':'sum'},
    )
    binned['rate'] = binned.fNumExcEvts / binned.fOnTimeAfterCuts * 3600
    max_rate = binned.groupby(level='fSourceName').aggregate({'rate': 'max'})
    return max_rate


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

    
skype = Skype4Py.Skype()
skype.Attach()
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
        try:
            skype.PlaceCall(my_phone_number)
        except Skype4Py.SkypeError:
            print('Could not call you, I\'ll try again in 10s')
            time.sleep(10)
            continue
        
        recieved_call = raw_input('Did your phone ring? (y/n): ')
        if recieved_call.lower()[0] == 'y':
            calling_worked = True	    

while True:
  try:
    print(weather.data())
    temperature = weather.data()[1]
    humidity_outside = weather.data()[3]
    wind_speed = weather.data()[5]
    wind_gusts = weather.data()[6]
    dimctrl_state = dimctrl.state()[0][:-1]
    print('\n', term.cyan(datetime.utcnow().strftime('%H:%M:%S:')))
    print('DimCtrl state:', dimctrl_state)
    print('Humidity: {:2.1f} %'.format(humidity_outside))
    print('Wind (gusts): {:2.1f} ({:1.2f}) km/h'.format(wind_speed, wind_gusts))
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
    qla_max_rates = get_max_rates()
    if qla_max_rates is None:
        print('No QLA data available yet')
    else: 
        print('max rates of today:')
        for source, rate in qla_max_rates.iterrows():
          rate = float(rate)
          if rate > max_rate[source]:
            max_rate[source] = rate
            if max_rate[source] > alert_rate[source]:
              msg = term.red('    !!!! Source {} over alert rate: {:3.1f} Events/h')
              raise ValueError(msg.format(source, max_rate[source]))
          print('{} : {:3.1f} Events/h'.format(source, max_rate[source]))
   # elif wind_gusts >= 40:
   #   mesg = term.red("    !!!! wind_gusts >= 40 km/h: {:2.1f}")
   #   raise ValueError(mesg.format(wind_gusts))
    print(term.green("Everything OK!"))
    time.sleep(delay_between_checks)
   
  except KeyboardInterrupt, SystemExit:
    raise 
  except Exception as e:
    print(e)
    called = False
    while not called:
      try:
        skype.PlaceCall(my_phone_number)
        called = True
      except Skype4Py.SkypeError:
        time.sleep(phone_ringing_time)

    time.sleep(delay_between_checks)
