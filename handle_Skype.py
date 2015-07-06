import time
import Skype4Py

phone_ringing_time = 15  # in sec. do not set larger than delay_between_checks.
delay_between_checks = 60  # in sec.

assert phone_ringing_time < delay_between_checks


def CallStatusText(status):
    return skype.Convert.CallStatusToText(status)


def OnCall(call, status):
    """ callback function (is called, whenever the state of the skypecall
        changes.

        (first if)
        It is basically making sure, that the shift_helper hangs up
        as soon as you or your answering machine or voicebox take the call.
        so the costs of these calls stay as low as possible.
        (second if)
        This makes sure, that the call is ended, after it was ringing 10sec
        (or a little less)
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
    CallStatus = status
    # print('Call status text: ', CallStatusText(status))
    if status == Skype4Py.clsInProgress:
        call.Finish()
    elif status == Skype4Py.clsEarlyMedia:
        time.sleep(phone_ringing_time)
        call.Finish()

skype = Skype4Py.Skype()
skype.Attach()
skype.OnCallStatus = OnCall


def call(my_phone_number):
    called = False
    while not called:
        try:
            skype.PlaceCall(my_phone_number)
            called = True
        except Skype4Py.SkypeError:
            time.sleep(phone_ringing_time)
