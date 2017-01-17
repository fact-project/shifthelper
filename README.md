# FACT shift helper

Monitor the First Cherenkov Telescope and alert the shifters or experts in case
something happens via:

* Phone
* Telegram Messenger 
* Email

# Deploy

Deployment instructions for the full shifthelper stack are in https://github.com/fact-project/shifthelper_deployment

## Environment variables

The logfile and config path can be set using the following env variables:

* `SHIFTHELPER_CONFIG=/path/to/config.json` sets the config file, 
if not set, the shifthelper expects it in `$HOME/.shifthelper/config.json`
* `SHIFTHELPER_LOGDIR=/path/to/dir` sets the directory for the two config files,
one human readable text file, one more machine readable `jsonlines` file.
* `SHIFTHELPER_DBCLONER_LOG=/path/to/logfile` sets the logfile for the `db_cloner` script.



# Shifthelper Guide

In order to avoid outdating documentation, we link here into the shifthelper source code.
We explain how to read it, thus you have always the most recent information, but don't have to search through the source code.

## Which conditions lead to a shifthelper call?

[You find the list of all checks here.](https://github.com/fact-project/shifthelper/blob/master/shifthelper/__main__.py#L58)

Background:
The shifthelper calls you, if a certain set of contidions is fulfilled.
An example would be to say: Call if the wind is very strong, while there is a shift and the telescope is not parked.
In code it looks like this:

    FactIntervalCheck(
        name='WindSpeedCheck',
        checklist=[
            conditions.is_shift_at_the_moment,
            conditions.is_high_windspeed,
            conditions.is_not_parked,
        ],
        category=CATEGORY_SHIFTER
    )
    
## How often are the checks performed?

The `FactIntervalCheck` base class predefines an interval [for all checks in seconds.]
(https://github.com/fact-project/shifthelper/blob/master/shifthelper/checks.py#L32)
However some checks are performed more or less often. The details one can find in 
[the list of all checks here.](https://github.com/fact-project/shifthelper/blob/master/shifthelper/__main__.py#L58)

## How long will I be called before the fallback shifter is called?

[This is defined here]
(https://github.com/fact-project/shifthelper/blob/master/shifthelper/notifiers.py#L16)

