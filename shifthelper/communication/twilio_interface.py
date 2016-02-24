# -*- coding:utf-8 -*-
from __future__ import absolute_import, print_function, division
from twilio.rest import TwilioRestClient

from .caller import Caller


class TwilioInterface(Caller):
    def __init__(self, phone_number, ring_time, sid, auth_token, twilio_number):
        self.client = TwilioRestClient(sid, auth_token)
        self.twilio_number = twilio_number
        super(TwilioInterface, self).__init__(phone_number, ring_time)

    def place_call(self):
        self.call = self.client.calls.create(
            url='http://fact-project.org/hangup.xml',
            to=self.phone_number,
            from_=self.twilio_number,
            timeout=self.ring_time,
        )

    def hangup(self):
        self.call.hangup()
