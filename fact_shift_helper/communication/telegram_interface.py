# -*- coding:utf-8 -*-
from __future__ import absolute_import, print_function, division
import requests
import json
from ..cli import ask_user


class TelegramInterface(object):
    url = 'https://api.telegram.org/bot{token}'

    def __init__(self, bot_token):
        self.url = self.url.format(token=bot_token)
        print('\nPlease visit www.telegram.me/factShiftHelperBot\n'
              'click on "SEND MESSAGE", the Telegram App will open.\n'
              'Send the message "/start" to the shiftHelperBot.\n'
              )

        confirmed = False
        while not confirmed:
            try:

                if ask_user('Did you send the /start command?'):
                    try:
                        self.chat_id, first, last = self.get_last_message_data()
                        print(u'Got a message from "{} {}"'.format(first, last))
                    except IndexError:
                        print('I did not receive a message.')
                        continue
                else:
                    continue
                confirmed = self.check_connection()
            except requests.exceptions.Timeout:
                print('Connection to Telegram timed out')

    def get_last_message_data(self):
        update = requests.get(self.url + '/getUpdates', timeout=5)
        update = json.loads(update.content.decode('utf8'))

        if update['ok']:
            chatdata = update['result'][-1]['message']['chat']
            chat_id = chatdata['id']
            firstname = chatdata['first_name']
            lastname = chatdata.get('last_name', '')
            return chat_id, firstname, lastname

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
