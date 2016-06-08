#!/usr/bin/env python
# coding: utf-8
'''
This script uses the fact twilio account to call a number.
If you provide a message with <message> this will be read to the
called person.

Usage:
    fact_call <phone_number> [<message>] [options]

Options:
    --ringtime=<N>   ringtime in seconds, defaults to value in the config file
'''
from docopt import docopt
import pkg_resources
from requests import Request

from . import read_config_file
from .. import TwilioInterface as Caller

__version__ = pkg_resources.require('shifthelper')[0].version


def main():
    args = docopt(
        __doc__,
        version=__version__,
    )
    config = read_config_file()

    if args['--ringtime']:
        ringtime = int(args['--ringtime'])
    else:
        ringtime = config.getint('caller', 'ringtime')

    caller = Caller(
        args['<phone_number>'],
        ringtime,
        config.get('twilio', 'sid'),
        config.get('twilio', 'auth_token'),
        config.get('twilio', 'number'),
    )

    # encode the url, this does not actually do the request
    if args['<message>']:
        r = Request(
            'GET',
            'http://twimlets.com/message',
            params={'Message': args['<message>']}
        )
        p = r.prepare()
        url = p.url
    else:
        url = None

    caller.place_call(url=url)


if __name__ == '__main__':
    main()
