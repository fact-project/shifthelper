import os
import datetime
from six.moves.configparser import SafeConfigParser
import pkg_resources
from getpass import getpass
from subprocess import check_call, CalledProcessError, PIPE
from fact_shift_helper import __version__

config_file = os.path.join(
    os.environ['HOME'],
    '.shifthelper/config-{}.ini'.format(__version__)
)


def night(timestamp=None):
    """
    gives the date for a day change at noon instead of midnight
    """
    if timestamp is None:
        timestamp = datetime.datetime.utcnow()
    if timestamp.hour < 12:
        timestamp = timestamp - datetime.timedelta(days=1)
    return timestamp


def night_integer(timestamp=None):
    """ get the correct night in fact format
        if it is after 0:00, take the date
        of yesterday
    """
    if timestamp is None:
        timestamp = datetime.datetime.utcnow()
    if timestamp.hour < 12:
        timestamp = timestamp - datetime.timedelta(days=1)
    night = int(timestamp.strftime('%Y%m%d'))
    return night


def decrypt_config_file():
    gpg_file = pkg_resources.resource_filename(__name__, 'config.gpg')
    print('You need to decrypt the config file.')
    passwd = getpass('Please enter the new FACT password\n> ')
    try:
        check_call(
            [
                'gpg',
                '-o',
                config_file,
                '--batch',
                '--passphrase',
                passwd,
                '--decrypt',
                gpg_file,

            ],
            stdout=PIPE, stderr=PIPE,

        )
    except CalledProcessError as e:
        if e.returncode == 2:
            raise OSError('You entered the wrong password')
        elif e.returncode == 127:
            raise OSError(
                'You need gpg installed to decrypt the config file'
            )
        else:
            raise


def read_config_file():
    if not os.path.isfile(config_file):
        decrypt_config_file()

    config = SafeConfigParser()
    config.optionxform = str
    list_of_successfully_parsed_files = config.read(config_file)
    if config_file not in list_of_successfully_parsed_files:
        raise Exception(
            'Could not read {0} succesfully.'.format(config_file)
        )
    return config
