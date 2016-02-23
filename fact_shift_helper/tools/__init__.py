import os
import datetime
from six.moves.configparser import SafeConfigParser
import requests
from getpass import getpass
from fact_shift_helper import __version__
import sys

config_file_name = 'config-{}.ini'.format(__version__)
config_file_path = os.path.join(
    os.environ['HOME'], '.shifthelper', config_file_name
)

remote_config_url = "https://fact-project.org/sandbox/shifthelper/config/{cn}".format(
    cn=config_file_name
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


def download_config_file():
    dotpath = os.path.join(os.environ['HOME'], '.shifthelper')
    if not os.path.exists(dotpath):
        os.makedirs(dotpath)

    passwd = getpass('Please enter the current FACT password')

    try:
        ret = requests.get(
            remote_config_url, auth=('FACT', passwd), verify=False
        )
        ret.raise_for_status()
    except requests.RequestException:
        if ret.status_code == 401:
            print('Wrong password')
        else:
            print('Could not download config file from fact-project.org')
        sys.exit()

    else:
        with open(config_file_path, 'wb') as f:
            f.write(ret.content)


def read_config_file():
    if not os.path.isfile(config_file_path):
        download_config_file()

    config = SafeConfigParser()
    config.optionxform = str
    list_of_successfully_parsed_files = config.read(config_file_path)
    if config_file_path not in list_of_successfully_parsed_files:
        raise Exception(
            'Could not read {0} succesfully.'.format(config_file_path)
        )
    return config
