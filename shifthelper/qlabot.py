#!/usr/bin/env python
# coding: utf-8
import requests
from os.path import expanduser
from datetime import datetime, timedelta
from collections import namedtuple
from threading import Thread, Event
import re
from time import sleep, gmtime
from .checks.qla import get_data, create_mpl_plot
from .tools import read_config_file, night
from functools import wraps
import logging
import pkg_resources
import os

__version__ = pkg_resources.require('shifthelper')[0].version
# setup logging


logdir = os.path.join(expanduser('~'), '.shifthelper')
if not os.path.exists(logdir):
    os.makedirs(logdir)

log = logging.getLogger('shifthelper')
log.setLevel(logging.INFO)
logfile_path = os.path.join(
    logdir, 'qla_bot_{:%Y-%m-%d}.log'.format(night()),
)
logfile_handler = logging.FileHandler(filename=logfile_path)
logfile_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    fmt='%(asctime)s - %(levelname)s - %(name)s | %(message)s',
    datefmt='%H:%M:%S',
)
formatter.converter = gmtime  # use utc in log
logfile_handler.setFormatter(formatter)
log.addHandler(logfile_handler)
log.addHandler(logging.StreamHandler())
logging.getLogger('py.warnings').addHandler(logfile_handler)
logging.captureWarnings(True)


qla_command = re.compile(
    '(/qla(@factShiftHelperBot)?)( [0-9]+)?( [0-9]{4}-[0-9]{2}-[0-9]{2})?'
)

Message = namedtuple(
    'Result', ['chat_id', 'update_id', 'text']
)

caption = 'Binning: {:2.0f} min, Night: {:%Y-%m-%d}'


def try_again(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        success = False
        tries = 0
        max_tries = 10
        while not success:
            if tries >= max_tries:
                raise requests.exceptions.ConnectionError(
                    'Could not conenct to Telegram'
                )
            try:
                ret = function(*args, **kwargs)
                success = ret.status_code == 200
            except requests.exceptions.ConnectionError:
                log.exception('Failed to conncet to Telegram')
                tries += 1
                sleep(5)
        return ret

    return wrapper


class QlaBot(Thread):
    url = 'https://api.telegram.org/bot{token}'

    def __init__(self, bot_token):
        self.url = self.url.format(token=bot_token)
        self.stop_event = Event()
        super().__init__()

    def run(self):
        while not self.stop_event.is_set():
            try:
                messages = self.get_messages()
            except:
                self.stop_event.wait(5)
                continue

            for message in messages:
                try:
                    match = qla_command.fullmatch(message.text)
                    if match:
                        self.confirm_message(message)
                        bin_width, timestamp = self.parse_command(match)
                        data = get_data(bin_width, timestamp)

                        if data is None:
                            self.send_message(
                                message.chat_id,
                                'No QLA data available for {:%Y-%m-%d}'.format(
                                    timestamp
                                )
                            )
                        else:
                            night = timestamp - timedelta(hours=12)
                            create_mpl_plot(data, '/tmp/qla.png')
                            with open('/tmp/qla.png', 'rb') as img:
                                self.send_image(
                                    message.chat_id,
                                    img,
                                    caption.format(bin_width, night),
                                )
                            log.info(
                                'send image for {:2.0f}, {:%Y-%m-%d}'.format(
                                    bin_width, timestamp
                                )
                            )
                    else:
                        if message.text.startswith('/qla'):
                            self.send_message(
                                message.chat_id,
                                'Could not parse your request, sorry!'
                            )
                except Exception as e:
                    log.exception(e)
                    self.send_message(
                        message.chat_id,
                        'Could not serve your request, sorry!'
                    )
            self.stop_event.wait(1)

    def parse_command(self, match):
        groups = match.groups()
        if groups[2] is None:
            bin_width = 20
        else:
            bin_width = float(groups[2].strip())
        if groups[3] is None:
            timestamp = datetime.utcnow()
            if 12 <= timestamp.hour <= 19:
                timestamp -= timedelta(days=1)
        else:
            timestamp = datetime.strptime(
                groups[3].strip(), '%Y-%m-%d'
            ) + timedelta(hours=20)

        return bin_width, timestamp

    def terminate(self):
        self.stop_event.set()

    @try_again
    def getUpdates(self):
        ret = requests.get(self.url + '/getUpdates', timeout=5)
        return ret

    def get_messages(self):

        ret = self.getUpdates().json()

        if ret['ok']:
            messages = []
            for update in ret['result']:
                message_data = update['message']
                chatdata = message_data['chat']

                message = Message(
                    update_id=update['update_id'],
                    chat_id=chatdata['id'],
                    text=message_data.get('text', ''),
                )
                messages.append(message)
            return messages

    @try_again
    def confirm_message(self, message):
        ret = requests.get(
            self.url + '/getUpdates',
            params={'offset': message.update_id + 1},
            timeout=5,
        )
        return ret

    @try_again
    def send_image(self, chat_id, image, caption=''):
        ret = requests.post(
            self.url + '/sendPhoto',
            data={'chat_id': chat_id, 'caption': caption},
            files={'photo': image},
            timeout=15,
        )
        return ret

    @try_again
    def send_message(self, chat_id, message):
        ret = requests.post(
            self.url + '/sendMessage',
            data={'chat_id': chat_id, 'text': message},
            timeout=5,
        )
        return ret


def main():
    config = read_config_file()
    bot = QlaBot(config.get('telegram', 'token'))
    bot.start()
    log.info('bot running')

    try:
        while True:
            sleep(10)
    except (KeyboardInterrupt, SystemExit):
        bot.terminate()


if __name__ == '__main__':
    main()
