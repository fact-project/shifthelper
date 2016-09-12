#!/usr/bin/env python
# coding: utf-8
from custos import Custos, TwilioNotifier, Message, levels
from time import sleep
import logging
from . import checks

log = logging.getLogger('custos')
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
log.addHandler(handler)


if __name__ == '__main__':
    
    twilio = 

    with Custos(
            checks=[
                checks.webdim.MainJsStatusCheck,
                checks.webdim.HumidityCheck,
                checks.webdim.WindSpeedCheck,
                checks.webdim.WindGustCheck,
                checks.webdim.MedianCurrentCheck,
                checks.webdim.MaximumCurrentCheck,
                checks.webdim.RelativeCameraTemperatureCheck,
            ],
            notifiers=[
                TwilioNotifier(
                    twilio_sid, twilio_auth_token, twilio_number,
                    ring_time=10,
                    recipients=('+492345', ),
                    level=levels.WARN,
                ),
            ],
            ) as custos:
        custos.run()

