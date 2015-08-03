from threading import Thread

class Check(Thread):
    def __init__(self, queue, interval, stop_event):
        self.queue = queue
        self.interval = interval
        self.stop_event = stop_event
        super(Check, self).__init__()

    def run(self):
        while not self.stop_event.is_set():
            self.check()
            self.stop_event.wait(self.interval)

    def check(self):
        raise NotImplementedError


class Alert(Thread):
    def __init__(self, queue, interval, stop_event):
        self.queue = queue
        self.interval = interval
        self.stop_event = stop_event

        super(Alert, self).__init__()

    def run(self):

        while not self.stop_event.is_set():
            while len(self.queue) > 0:
                print(self.queue.popleft())
            self.stop_event.wait('interval')
