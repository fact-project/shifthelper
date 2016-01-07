# -*- coding:utf-8 -*-
from __future__ import absolute_import, print_function, division
import requests
from datetime import datetime
from ..cli import ask_user
from collections import namedtuple

Message = namedtuple(
    'Result', ['chat_id', 'update_id', 'firstname', 'lastname', 'date']
)


class TelegramInterface(object):
    url = 'https://api.telegram.org/bot{token}'

    def __init__(self, bot_token):
        self.url = self.url.format(token=bot_token)
        print('\nPlease visit www.telegram.me/factShiftHelperBot\n'
              'click on "SEND MESSAGE", the Telegram App will open.\n'
              'Send the message "/start" to the shiftHelperBot.\n'
              )

        confirmed = False
        correct_user = False
        while not confirmed or not correct_user:
            try:
                if ask_user('Did you send the /start command?'):
                    message = self.get_last_message()
                    if message is None:
                        print('I did not receive a message.')
                    else:
                        msg = u'Got a message from "{m.firstname} {m.lastname}"'
                        print(msg.format(m=message))
                        correct_user = ask_user('Is that you?')
                        self.chat_id = message.chat_id
                if correct_user:
                    confirmed = self.check_connection()
            except requests.exceptions.Timeout:
                print('Connection to Telegram timed out')

    def get_last_message(self):
        ret = requests.get(self.url + '/getUpdates', timeout=5).json()

        if ret['ok']:
            if len(ret['result']) == 0:
                return None
            update = ret['result'][-1]
            message_data = update['message']
            chatdata = message_data['chat']

            message = Message(
                update_id=update['update_id'],
                chat_id=chatdata['id'],
                firstname=chatdata['first_name'],
                lastname=chatdata.get('last_name', ''),
                date=datetime.fromtimestamp(message_data['date']),
            )
            self.confirm_message(message)
            return message

    def confirm_message(self, message):
        requests.get(
            self.url + '/getUpdates',
            params={'offset': message.update_id + 1},
            timeout=5,
        )

    def send_image(self, image):
        try:
            r = requests.post(
                self.url + '/sendPhoto',
                data={'chat_id': self.chat_id},
                files={'photo': image},
                timeout=15,
            )
        except requests.exceptions.Timeout:
            print('Telegram "send_message" timed out')
        return r

    def send_message(self, message):
        try:
            r = requests.post(
                self.url + '/sendMessage',
                data={'chat_id': self.chat_id, 'text': message},
                timeout=5,
            )
        except requests.exceptions.Timeout:
            print('Telegram "send_message" timed out')
        return r

    def check_connection(self):
        print('I will send you a message now.')
        self.send_message('Welcome to the shift, I wish a pleasant night!')
        return ask_user('Did you receive it?')
