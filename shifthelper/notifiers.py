from queue import Queue, Empty
from collections import Mapping
import datetime

from custos import TwilioNotifier
from .tools.whosonshift import whoisonshift


class FactTwilioNotifier(TwilioNotifier):
    def __init__(self, time_before_fallback=datetime.timedelta(minutes=10), *args, **kwargs):
        self.time_before_fallback = time_before_fallback
        self.not_acknowledged_calls = []
        self.nobody_is_listening = False
        super().__init__(*args, **kwargs)

    def notify(self, recipient, msg):
        self._remove_acknowledged_calls()
        super().notify(recipient, msg)
        self.not_acknowledged_calls.append((self.call, msg))

    def _remove_acknowledged_calls(self):
        """ from the list of not acknowledged calls
        remove all calls, which have been "completed",
        i.e. a person has taken the call

        remove also all calls, whose message.check is 
        equal to a call, which has been taken.
        """
        acknowledged_checks = set()
        for call, msg in self.not_acknowledged_calls[:]:
            call.update_instance()
            if call.status in ["completed"]:
                acknowledged_checks.add(msg.check)
                self.not_acknowledged_calls.remove((call, msg))

        for call, msg in self.not_acknowledged_calls[:]:
            if msg.check in acknowledged_checks:
                self.not_acknowledged_calls.remove((call, msg))

    def _get_oldest_call_age(self):
        max_age = datetime.timedelta()
        for call, msg in self.not_acknowledged_calls:
            age = datetime.datetime.utcnow() - msg.timestamp
            if age > max_age:
                max_age = age
        return max_age


    def phone_number_of_normal_shifter(self):
        return '+41774528842'
        return whoisonshift().iloc[0].phone_mobile

    def phone_number_of_fallback_shifter(self):
        return '+41774528842'
        return whoisonshift().iloc[0].phone_mobile


    def handle_message(self, msg):
        if msg.level >= self.level:
            if self._get_oldest_call_age() < self.time_before_fallback:
                phone_number = self.phone_number_of_normal_shifter()
            else:
                phone_number = self.phone_number_of_fallback_shifter()

            try:
                self.notify(phone_number, msg)
            except:
                log.exception('Could not notifiy recipient {}'.format(phone_number))
