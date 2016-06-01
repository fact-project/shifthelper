import os
import datetime
from six.moves.configparser import SafeConfigParser
import requests
from getpass import getpass
import sys
import pkg_resources
import sqlalchemy
from ..config import config

__version__ = pkg_resources.require('shifthelper')[0].version


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


def create_db_connection():
    db_config = config['database']
    factdb = sqlalchemy.create_engine(
        "mysql+pymysql://{user}:{pw}@{host}/{db}".format(
            user = db_config['user'],
            pw = db_config['password'],
            host = db_config['host'],
            db = db_config['database'],
        )
    )
    return factdb
