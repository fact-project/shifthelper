# -*- coding:utf-8 -*-
from __future__ import absolute_import, print_function, division
from twilio.rest import TwilioRestClient

from .caller import Caller
import logging

from .. import tools
import time
from ..config import config

log = logging.getLogger(__name__)

class TwilioInterface(Caller):
    def __init__(self, phone_number):
        twilio = config['twilio']
        self.client = TwilioRestClient(twilio['sid'], twilio['auth_token'])
        self.twilio_number = twilio['number']
        super().__init__(phone_number, ring_time=5)

    def place_call(self):
        start_time= time.time()
        self.call = self.client.calls.create(
            url="http://twimlets.com/message?Message%5B0%5D=This%20is%20a%20FACT%20Alert%20Wake%20up&",
            to=self.phone_number,
            from_=self.twilio_number,
            timeout=self.ring_time,
            if_machine="Hangup",
        )
        call = self.call

        while True:
            call.update_instance()
            if call.status not in [call.QUEUED, call.RINGING, call.IN_PROGRESS]:
                break
        call.update_instance()
        stop_time = time.time()
        duration = stop_time - start_time

        return {
            "status": call.status,
            "duration": call.duration,
            "answered_by": call.answered_by,
        }


    def hangup(self):
        self.call.hangup()
