#!/usr/bin/env python
'''
Switch on or off the IR cams

Usage:
    fact_ircam on
    fact_ircam off
'''
from __future__ import print_function
from six.moves import input
import requests
from getpass import getpass
from docopt import docopt
import sys

URL = 'https://fact-project.org/cam/ir/index.php'


def change_ir_setting(action='off'):
    assert action in ['on', 'off']

    user = input('Username: ')
    passwd = getpass()

    ret = requests.post(
        URL,
        auth=(user, passwd),
        params={'action': action},
        verify=False,
    )
    return ret


def main():
    args = docopt(__doc__)

    if args['on']:
        ret = change_ir_setting(action='on')
        if ret.status_code == 200:
            print('IR Mode should be on, check Camera Image')
            print('http://fact-project.org/cam/index.php')
    elif args['off']:
        ret = change_ir_setting(action='off')
        if ret.status_code == 200:
            print('IR Mode should be off, check Camera Image')
            print('http://fact-project.org/cam/index.php')

    if ret.status_code == 401:
        print('Authentification failure', file=sys.stderr)
        sys.exit(1)
    elif ret.status_code != 200:
        print('Could not change settings')
        sys.exit(2)


if __name__ == '__main__':
    main()