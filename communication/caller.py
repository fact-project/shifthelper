# -*- coding:utf-8 -*-
from __future__ import absolute_import, print_function, division


class Caller(object):
    def __init__(self, phone_number, ring_time):
        self.ring_time = ring_time
        self.phone_number = phone_number

    def hangup(self):
        raise NotImplementedError

    def place_call(self):
        raise NotImplementedError
