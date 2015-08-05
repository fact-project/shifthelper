from threading import Thread
from blessings import Terminal
from datetime import datetime



class StatusDisplay(Thread):

    def __init__(self, qla_data, status_data, stop_event):
        self.status_data = status_data
        self.qla_data = qla_data
        self.term = Terminal()
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            self.update_status()
            self.stop_event.wait(1)

    def update_status(self):
        with self.term.fullscreen(), self.turn.hide_cursor():
            self.term.clear()
            print(self.term.cyan(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            with self.term.position(0, 2):
                print('System Status')
                for key, val in self.status_data.iteritems():
                    print(u'{:<20}  {:6>} {:<6}'.format(key, *val))
            with self.term.position(40, 2):
                print('Maximum Source Activity')
                for key, val in self.qla_data.iteritems():
                    print(self.term.move_x(40) + u'{:<20}  {:6>} {:<6}'.format(
                        key, *val
                    ))
