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
At first start of the shift_helper you will be asked for the well known password
to decrypt those credentials

# Install 

We strongly recommend installing `python3` via [Anaconda](https://www.continuum.io/downloads). 
Available for OSX and Linux.

You can install the bleeding edge version of the `shift_helper` like this:

```bash
pip install https://github.com/fact-project/shifthelper/archive/v0.4.0.tar.gz
```

# Use


Just start the `shift_helper` executable, it's in your path after you installed the packages.
Invoke it e.g. like this

```bash
shift_helper +4123456789
```


# Uninstall

```
pip uninstall shifthelper
```

### Developers: Create the config.gpg

    gpg --cipher-algo AES256 --symmetric config.ini
