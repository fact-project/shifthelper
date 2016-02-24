# -*- coding:utf-8 -*-
from __future__ import absolute_import, print_function, division

import plivo
from .caller import Caller

class PlivoInterface(Caller):

    def __init__(self, phone_number, ring_time, auth_id, auth_token, plivo_number):
        self.rest_api = plivo.RestAPI(auth_id, auth_token)
        self.plivo_number = plivo_number
        super(PlivoInterface, self).__init__(phone_number, ring_time)

    def place_call(self):
        self.call = self.rest_api.Call.send(
            src=self.plivo_number, 
            to=self.phone_number,
            answer_url="http://fact-project.org/hangup.xml",
            hangup_on_ring=self.ring_time,
            )

    def hangup(self):
        self.rest_api.hangup_request(params=self.call.json_data)