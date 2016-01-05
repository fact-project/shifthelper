import os
import datetime
from six.moves.configparser import SafeConfigParser
import pkg_resources
from getpass import getpass
from subprocess import Popen, CalledProcessError, PIPE
from fact_shift_helper import __version__

config_file_path = os.path.join(
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


def let_user_decrypt_config_file():
    decrypt_config_file(
        passphrase=query_user_for_config_passphrase())


def query_user_for_config_passphrase():
    print('You need to decrypt the config file.')
    return getpass('Please enter the new FACT password\n> ')


def decrypt_config_file(
        passphrase,
        input_path=pkg_resources.resource_filename(__name__, 'config.gpg'),
        output_path=config_file_path
        ):

    process = Popen(
        [
            'gpg',
            '-o',
            output_path,
            '--batch',
            '--passphrase-fd',
            '0',
            '--decrypt',
            input_path,
        ],
        stdout=PIPE, stderr=PIPE, stdin=PIPE,
    )
    out, err = process.communicate(input=passphrase.encode('utf-8'))

    if process.returncode != 0:
        if process.returncode == 2:
            raise OSError('Wrong password, try again please.')
        else:
            raise OSError(err)


def read_config_file():
    if not os.path.isfile(config_file_path):
        let_user_decrypt_config_file()

    config = SafeConfigParser()
    config.optionxform = str
    list_of_successfully_parsed_files = config.read(config_file_path)
    if config_file_path not in list_of_successfully_parsed_files:
        raise Exception(
            'Could not read {0} succesfully.'.format(config_file_path)
        )
    return config
