# FACT shift helper

* Calls you via twilio if security limits are
reached, data taking stopped or the QLA exceeds alert limits

* just enter your phone number, check for the incoming
call

* go to bed

You can give the number directly as firs command line option

# the config file

Credentials and other config data is stored in the config.ini file
a dummy is stored in the config_example.ini

# Install 

	pip install git+https://bitbucket.org/dneise/fact_shift_helper#egg=fact_shift_helper

# Uninstall

	pip uninstall fact_shift_helper

### Developers: Create the config.gpg

    gpg --cipher-algo AES256 --symmetric config.ini