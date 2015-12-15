import os
import datetime
from six.moves.configparser import SafeConfigParser
import pkg_resources
import shutil
from subprocess import check_call, CalledProcessError
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


def read_config_file():
    if not os.path.isfile(config_file):
        shutil.copyfile(
            src=pkg_resources.resource_filename(__name__, 'config.gpg'),
            dst=config_file.replace('.ini', '.gpg'),
        )
        try:
            check_call([
                'gpg',
                '-o',
                config_file,
                '--decrypt',
                config_file.replace('.ini', '.gpg'),
            ])
        except CalledProcessError:
            raise OSError('You need gpg installed to decrypt the config file')

    config = SafeConfigParser()
    config.optionxform = str
    list_of_successfully_parsed_files = config.read(config_file)
    if config_file not in list_of_successfully_parsed_files:
        raise Exception(
            'Could not read {0} succesfully.'.format(config_file)
        )
    return config
