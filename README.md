# FACT shift helper

* Calls you on your phone if security limits are
reached, data taking stopped or the QLA exceeds alert limits

* Sends you messages and QLA plots via Telegram Messenger

* Just enter your phone number, check for the incoming call

* Send the `/start` message to the @factShiftHelperBot

You can also give the number directly as first command line argument

# the config file

The shift_helper needs some credentials, for example database access to
monitor the QLA results.
At first start of the shift_helper you will be asked for the well known password
to decrypt those credentials

# Install 

We recommend to install `python3` via `anaconda3`: https://www.continuum.io/downloads

```
pip install http://fact-project.org/sandbox/shifthelper/fact_shift_helper-0.3.4.tar.gz
```

# Use

Just start the `shift_helper` executable, it's in your path after 
you installed the packages


# Uninstall

```
pip uninstall fact_shift_helper
```

### Developers: Create the config.gpg

    gpg --cipher-algo AES256 --symmetric config.ini
