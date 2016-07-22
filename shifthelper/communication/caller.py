class Caller(object):
    def __init__(self, phone_number, ring_time=20):
        self.ring_time = ring_time
        self.phone_number = phone_number

    def hangup(self):
        raise NotImplementedError

    def place_call(self):
        raise NotImplementedError


class NoCaller(Caller):
    """ Dummy caller for debugging only """
    def __init__(self, *args, **kwargs):
        self.phone_number = "nothing"
        pass

    def hangup(self):
        pass

    def place_call(self):
        pass
