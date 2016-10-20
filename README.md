# FACT shift helper

* Calls you on your phone if security limits are
reached, data taking stopped or the QLA exceeds alert limits

    * Just enter your phone number
    * It will call you once at startup for verification.

* *If you want*, it sends you messages and QLA plots via [Telegram Messenger App](https://telegram.org/)

    * Send the `/start` message to the [@factShiftHelperBot](https://telegram.me/factShiftHelperBot) in order to tell it, you are the shifter for tonight.


# the config file

The shift_helper needs some credentials, for example database access to
monitor the QLA results.
At first start of the shifthelper you will be asked for the well known password
to download these credentials.

# Deploy

1. Clone the repo and checkout the latest release
2. Use the provided conda_env.yaml to setup a conda env with all dependencies:
```
conda env create -n shifthelper -f conda_env.yaml
source activate shifthelper
```
3. Get the config.json file from the shifthelper-config repo and put it into
   ~/.shifthelper/config.json

4. Install the packages:
```
pip install https://github.com/fact-project/smart_fact_crawler/archive/v0.2.1.tar.gz
pip install .
```
