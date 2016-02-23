import os
import datetime
from six.moves.configparser import SafeConfigParser
import pkg_resources
from getpass import getpass
from subprocess import Popen, PIPE
from fact_shift_helper import __version__

config_file_name = 'config-{}.ini'.format(__version__) 
config_file_path = os.path.join(
    os.environ['HOME'],'.shifthelper', config_file_name)

remote_config_file_location = "{host}:{path}/{cn}".format(
    host="fact-project.org",
    path="/home/dneise/shifthelper",
    cn=config_file_name)

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

    command = "scp {remote} {local}".format(
        remote=remote_config_file_location,
        local=dotpath)
    print("Trying to do\n   {}".format(command))
    os.system(command)

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
