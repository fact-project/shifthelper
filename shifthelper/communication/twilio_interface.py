# -*- coding:utf-8 -*-
from __future__ import absolute_import, print_function, division
from twilio.rest import TwilioRestClient

from .caller import Caller
import logging

from .. import tools
import time
from ..config import config

class TwilioInterface(Caller):
    def __init__(self, phone_number):
        twilio = config['twilio']
        sid = twilio['sid']
        auth_token = twilio['auth_token']
        twilio_number = twilio['number']
        ring_time = 20

        self.client = TwilioRestClient(sid, auth_token)
        self.twilio_number = twilio_number
        self.logger = logging.getLogger("shift_helper")
        super().__init__(phone_number, ring_time)

    def place_call(self):
        self.logger.debug("placing call")
        start_time= time.time()
        self.call = self.client.calls.create(
            url="http://twimlets.com/message?Message%5B0%5D=This%20is%20a%20FACT%20Alert%20Wake%20up&",
            to=self.phone_number,
            from_=self.twilio_number,
            timeout=self.ring_time,
            #if_machine="Hangup",
        )
        call = self.call

        self.logger.debug("call.sid {0!s}".format(call.sid))

        while True:
            call.update_instance()
            if call.status not in [call.QUEUED, call.RINGING, call.IN_PROGRESS]:
                    break
        call.update_instance()
        stop_time = time.time()
        duration = stop_time - start_time

        self.logger.debug("call ended with status: {0!s}".format(call.status))
        self.logger.debug("measured complete duration: {0!s} seconds".format(duration))
        self.logger.debug("call.duration: {0!s}".format(call.duration))
        self.logger.debug("answered_by: {0!s}".format(call.answered_by))


    def hangup(self):
        self.call.hangup()
