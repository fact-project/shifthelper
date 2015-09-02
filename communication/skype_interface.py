# -*- coding:utf-8 -*-
from __future__ import absolute_import, print_function, division
import Skype4Py
import time

from .caller import Caller


class SkypeInterface(Caller):

    def __init__(self, phone_number, ring_time):
        self.skype = Skype4Py.Skype(Transport='x11')
        self.skype.Attach()
        self.skype.OnCallStatus = self.on_call
        super(SkypeInterface, self).__init__(phone_number, ring_time)

    def hangup(self):
        try:
            if self.call is not None:
                self.call.Finish()
                self.call = None
        except Skype4Py.SkypeError as e:
            if '[Errno 559]' in e.message:
                pass

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
        try:
            if status == Skype4Py.clsInProgress:
                call.Finish()
            elif status in [Skype4Py.clsEarlyMedia, Skype4Py.clsRinging]:
                time.sleep(self.ring_time)
                call.Finish()
        except Skype4Py.SkypeError as e:
            if '[Errno 559]' in e.message:
                pass

    def place_call(self):
        called = False
        while not called:
            try:
                self.call = self.skype.PlaceCall(self.phone_number)
                called = True
            except Skype4Py.SkypeError:
                mesg = 'Calling impossible, trying again in {:1.1f} seconds'
                print(mesg.format(self.ring_time))
                time.sleep(self.ring_time)


