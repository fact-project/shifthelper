#!/usr/bin/env python
# coding: utf-8
'''
This script uses the fact twilio account to call a number.

Logs are stored in ~/.shifthelper

Usage:
    fact_call <phone_number> [options]
'''
from docopt import docopt
import pkg_resources

from . import read_config_file
from .. import TwilioInterface as Caller

__version__ = pkg_resources.require('shifthelper')[0].version


def main():
    args = docopt(
        __doc__,
        version=__version__,
    )
    config = read_config_file()

    caller = Caller(
        args['<phone_number>'],
        config.getint('caller', 'ringtime'),
        config.get('twilio', 'sid'),
        config.get('twilio', 'auth_token'),
        config.get('twilio', 'number'),
    )
    caller.place_call()


if __name__ == '__main__':
    main()
