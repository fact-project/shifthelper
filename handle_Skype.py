import time
import Skype4Py

ringing_time = None  # in sec. do not set larger than delay_between_checks.
skype = None


def setup(args):
    global skype
    global ringing_time
    ringing_time = args['--ringtime']
    skype = Skype4Py.Skype(Transport='x11')
    skype.Attach()
    skype.OnCallStatus = OnCall


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
        time.sleep(ringing_time)
        call.Finish()


def call(my_phone_number):
    called = False
    while not called:
        try:
            skype.PlaceCall(my_phone_number)
            called = True
            time.sleep(ringing_time)
        except Skype4Py.SkypeError:
            mesg = 'Calling impossible, trying again in {:1.1f} seconds'
            print(mesg.format(ringing_time))
            time.sleep(ringing_time)
