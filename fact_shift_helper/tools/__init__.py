import os
import datetime
from ConfigParser import SafeConfigParser
import pkg_resources
import shutil

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

def read_config_file(config_file_name):

    if os.path.isfile( os.path.join(os.getcwd(), config_file_name)):

        config = SafeConfigParser()
        list_of_successfully_parsed_files = config.read(config_file_name)
        if config_file_name not in list_of_successfully_parsed_files:
            raise Exception('Could not read {0} succesfully.'.format(config_file_name) )
        return config

    else:
        shutil.copyfile(src=pkg_resources.resource_filename(__name__, 'config.gpg'), 
                        dst=os.path.join(os.getcwd(), 'config.ini')
            )

        raise IOError('\n'
                '\tYou need to decrypt the config file using: \n'
                '\t$ gpg -o config.ini --decrypt config.gpg \n'
                '\tYou will be asked for a password, enter the new FACT password'
            )