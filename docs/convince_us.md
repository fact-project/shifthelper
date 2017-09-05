# Shifthelper report 05.09.2017

D.Neise

# What's checked?

| Name                           | limit        | Interval[s] | conditions                     |
|--------------------------------|--------------|-------------|--------------------------------|
| SmartFactUpToDate              | > 10 min     | 120         | only during shift              |
| ParkingChecklistFilled         | after 10min  | 120         | only **outside** shift         |
| IsUserAwakeBeforeShutdown      | 20min before | 120         | only during shift              |
| MAGICWeatherUpToDate           | > 10 min     | 120         | only during shift              |
| Shifter in shift scheduler     |              | 120         | only during shift              |
| MainJsStatusCheck              | Running?     | 120         | only during shift              |
| WindSpeedCheck                 | > 50 km/h    | 120         | only during shift & not parked |
| WindGustCheck                  | > 50 km/h    | 120         | only during shift & not parked |
| MedianCurrentCheck             | > 115 uA     | 120         | only during shift              |
| MaximumCurrentCheck            | > 160 uA     | 120         | only during shift              |
| RelativeCameraTemperatureCheck | > 15.0°C     | 120         | only during shift              |
| BiasNotOperatingDuringDataRun  |              | 120         | only during shift              |
| BiasChannelsInOverCurrent      |              | 120         | only during shift              |
| BiasVoltageNotAtReference      |              | 120         | only during shift              |
| ContainerTooWarm               | > 42°C       | 120         | only during shift              |
| DriveInErrorDuringDataRun      |              | 120         | only during shift              |
| BiasVoltageOnButNotCalibrated  |              | 120         | only during shift              |
| DIMNetworkNotAvailable         |              | 120         | only during shift              |
| NoDimCtrlServerAvailable       |              | 120         | only during shift              |
| TriggerRateLowForTenMinutes    | < 1/sec      | 120         | only during shift              |
| Flare                          | (individual) | 300         |                                |

# Experience?

Shifthelper is running unmodified since 23.07.2017

## 24.07. Remove unnecessary fallback calls:

Under certain conditions acknowledged alerts were not being removed form the alert list
and thus the fallback was called unnecessaringly.

At the same moment, a more severe bug was found an removed. In case the call
to the shifter threw an exception, the fallback was not called.
An exception was raised, because the number to be called was an
international number from a country our Twilio contract was (for security reasons)
not allowed to make calls to. Now we may make calls to the whole world. This bug was found using the test call during startup. Making test calls (DummyAlert) is a part of the startup checklist.

## 17.07. Fix cache misses

This lead to expert calls about every 200 minutes.
Using a different cache library fixed these.


## 19.04. Fix connection timeouts of the mysql db

These lead to expert calls. Recycling the connection pool fixed these.

## 13.04. Multiple:

 * set smart_fact_crawler timeout = 5 seconds
        --> expert calls when smart_fact cannot be seen.
 * Fix cloning of local DB copy --> lead to expert calls

## 28.02. Allow shifters to change their phone numbers.

The shifter contact DB was cloned only once at SH startup. So changes in contact
details would require a SH restart.

## 06.02. Fix Flare Alerts

 * In case of FlareAlert a shifter was called without end.
 * Fallback shifter was not called in this case.


# How is it running?

Shifthelper is running in one of two places:

 * Either the Rancher cloud at TU Dortmund (https://shifthelper.app.tu-dortmund.de/)
 * Or on a desktop PC at ETH Zurich (https://ihp-pc41.ethz.ch/)

The shifhelper runs two processes in supervised containers which get restatred when they crash ([Docker container](https://www.docker.com/)):

 * shifthelper
 * webinterface

In case the webinterface gets DDOSed, the shifthelper still runs and calls people,
but they cannot acknowledge the calls anymore. Very annoying but at least safe.
