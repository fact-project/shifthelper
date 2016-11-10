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
