# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
import requests
import json
from blessings import Terminal

term = Terminal()

bot_token = '<botoken>'
url = 'https://api.telegram.org/bot{}'.format(bot_token) + '/{method}'
chat_id = None


def get_last_message_data():
    update = requests.get(url.format(method='getUpdates'))
    update = json.loads(update.content.decode('utf8'))

    if update['ok']:
        chatdata = update['result'][-1]['message']['chat']
        chat_id = chatdata['id']
        firstname = chatdata['first_name']
        if 'lastname' in chatdata:
            lastname = chatdata['last_name']
        else:
            lastname = ''
        return chat_id, firstname, lastname


def send_message(message):
    r = requests.post(
        url.format(token=bot_token, method='sendMessage'),
        data={'chat_id': chat_id, 'text': message},
    )
    return r


def setup(use_telegram=False):
    print(term.cyan('\nTelegram Setup'))
    if not use_telegram:
        use_tg = raw_input(
            'Do you want to use Telegram to get error messages? (y/n):'
        )
        if not use_tg.lower()[0] == 'y':
            return False

    print('\nPlease visit www.telegram.me/factShiftHelperBot\n'
          'click on "SEND MESSAGE", the Telegram App will open.\n'
          'Send the message "/start" to the shiftHelperBot.\n'
          )

    global chat_id

    confirmed = False
    while not confirmed:
        send_start = raw_input('Did you send the /start command? (y/n):')
        if send_start.lower()[0] == 'y':
            chat_id, firstname, lastname = get_last_message_data()
            print('Got a message from "{} {}"'.format(firstname, lastname))
        else:
            continue
        confirmed = check_connection()
        if not confirmed:
            ask_again = raw_input('Try again? (y/n):')
            if not ask_again.lower()[0] == 'y':
                return False
    return True


def check_connection():
    print('I will send you a message now.')
    send_message('Welcome to the shift, I wish a pleasant night!')
    received = raw_input('Did you receive it? (y/n):')
    if received.lower()[0] == 'y':
        return True
    return False
