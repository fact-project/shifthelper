# -*- coding:utf-8 -*-
from __future__ import absolute_import, print_function, division
import time
import Skype4Py
import requests
import json
from blessings import Terminal

term = Terminal()

class SkypeInterface(object):

    def __init__(self, args):
        self.ringing_time = args['--ringtime']
        self.skype = Skype4Py.Skype(Transport='x11')
        self.skype.Attach()
        self.skype.OnCallStatus = self.on_call

    def call_status_text(self, status):
        return self.skype.Convert.CallStatusToText(status)

    def on_call(self, call, status):
        """ callback function (is called, whenever the state of the skypecall
            changes.

            (first if)
            It is basically making sure, that the shift_helper hangs up
            as soon as you or your answering machine or voicebox take the call.
            so the costs of these calls stay as low as possible.
            (second if)
            This makes sure, that the call is ended, after it was ringing
            for ringing time
            The reason for this is the following:
            When I drop the call on my cell-phone, the call would actually be
            diverted to my voicebox. So the connection gets established.
            Then the shift_helpers call is connected to my voicebox.
            Nobody is saying anything, but the call will still cost money.
            That alone is no problem.
            But after 30sec the shift_helper would again try to place a call ...
            while another call is still active, which leads to an exception,
            which is not handled at the moment (FIXME)
        """
        if status == Skype4Py.clsInProgress:
            call.Finish()
        elif status in [Skype4Py.clsEarlyMedia, Skype4Py.clsRinging]:
            time.sleep(self.ringing_time)
            call.Finish()


    def place_call(self, my_phone_number):
        called = False
        while not called:
            try:
                self.skype.PlaceCall(my_phone_number)
                called = True
            except Skype4Py.SkypeError:
                mesg = 'Calling impossible, trying again in {:1.1f} seconds'
                print(mesg.format(self.ringing_time))
                time.sleep(self.ringing_time)


class TelegramInterface(object):
    url = 'https://api.telegram.org/bot{token}'

    def __init__(self, bot_token):
        self.url = self.url.format(bot_token)
        print('\nPlease visit www.telegram.me/factShiftHelperBot\n'
              'click on "SEND MESSAGE", the Telegram App will open.\n'
              'Send the message "/start" to the shiftHelperBot.\n'
              )

        confirmed = False
        while not confirmed:
            try:
                send_start = raw_input('Did you send the /start command? (y/n):')
                if send_start.lower()[0] == 'y':
                    self.chat_id, first, last = self.get_last_message_data()
                    print('Got a message from "{} {}"'.format(first, last))
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
        received = raw_input('Did you receive it? (y/n):')
        if received.lower()[0] == 'y':
            return True
        return False
