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

# Use

Call the `shift_helper` from a dedicated folder:

    $ mkdir shift_helper_dir
    $ cd shift_helper_dir
    $ shift_helper [--help]

Have a look at the `--help` page if you like to learn more about the available Options.

If you use it for the **first time** the helper will complain about a missing `config.ini` File. In order to make life easier for you, we provided an encrypted default config-file, which you just need to decrypt, using the password you all know. 

# Uninstall

	pip uninstall fact_shift_helper

### Developers: Create the config.gpg

    gpg --cipher-algo AES256 --symmetric config.ini