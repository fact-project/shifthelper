from threading import Thread
from blessings import Terminal
from datetime import datetime

def timestamp():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')


class StatusDisplay(Thread):

    def __init__(self, qla_data, status_data, stop_event):
        self.status_data = status_data
        self.qla_data = qla_data
        self.term = Terminal()
        self.term.clear()
        self.stop_event = stop_event
        super(StatusDisplay, self).__init__()

    def run(self):
        with self.term.fullscreen(), self.term.hidden_cursor():
            while not self.stop_event.is_set():
                self.update_status()
                self.stop_event.wait(1)

    def update_status(self):
        print(self.term.move(0, 0) + self.term.cyan(timestamp()))

        print(self.term.move(2, 0) + 'System Status')
        for i, (key, val) in enumerate(self.status_data.iteritems()):
            print(self.term.move(3+i, 0) + u'{:<20}  {:6>} {:<6}'.format(
                key, *val
            ))

        print(self.term.move(2, 40) + 'Maximum Source Activity')
        for i, (key, val) in enumerate(self.qla_data.iteritems()):
            print(self.term.move(3+i, 40) + u'{:<20}  {:6>} {:<6}'.format(
                key, *val
            ))
