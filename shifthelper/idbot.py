#!/usr/bin/env python
# coding: utf-8
import requests
from datetime import datetime, timedelta
from collections import namedtuple
from threading import Thread, Event
import re
from time import sleep, gmtime
from .checks.qla import get_data, create_mpl_plot
from .tools import night
from functools import wraps
import logging
import pkg_resources
import os
from shifthelper.config import config


print(__name__)
log = logging.getLogger(__name__)

qla_command = re.compile(
    '(/id(@factShiftHelperBot)?)'
)

Message = namedtuple(
    'Result', ['chat_id', 'update_id', 'text']
)


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
                    print(message)
                    if match:
                        self.confirm_message(message)
                        self.send_message(message.chat_id,
                            "your telegram id is:"+str(message.chat_id))
                except Exception as e:
                    log.exception(e)
                    self.send_message(
                        message.chat_id,
                        'Could not serve your request, sorry!'
                    )
            self.stop_event.wait(1)

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
    bot = QlaBot(config['telegram']['token'])
    bot.start()
    log.info('bot running')

    try:
        while True:
            sleep(10)
    except (KeyboardInterrupt, SystemExit):
        bot.terminate()


if __name__ == '__main__':
    main()
