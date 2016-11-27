import datetime

from custos import TwilioNotifier
from .tools.whosonshift import whoisonshift
from .tools import config

import logging
log = logging.getLogger(__name__)


class FactTwilioNotifier(TwilioNotifier):
    def __init__(self,
                 time_before_fallback=datetime.timedelta(minutes=10),
                 *args,
                 **kwargs):
        self.time_before_fallback = time_before_fallback
        self.not_acknowledged_calls = []
        self.nobody_is_listening = False
        self.twiml == 'hangup'

        # actual recipients are determinded in
        # handle_message() using phone_number_of...()
        kwargs["recipients"] = []
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
        try:
            return whoisonshift().phone_mobile
        except IndexError:
            return config['developer']['phone_number']

    def phone_number_of_fallback_shifter(self):
        return config['fallback_shifter']['phone_number']
        try:
            return whoisonshift().phone_mobile
        except IndexError:
            return config['developer']['phone_number']

    def handle_message(self, msg):
        log.debug('Got a message')
        if msg.level >= self.level:
            log.debug('Message is over alert level')

            if msg.category == 'check_error':
                log.debug('Message has category "check_error"')
                phone_number = config['developer']['phone_number']
            else:
                if self._get_oldest_call_age() < self.time_before_fallback:
                    log.debug('Getting phone number of primary shifter')
                    phone_number = self.phone_number_of_normal_shifter()
                else:
                    log.debug('Getting phone number of fallback shifter')
                    phone_number = self.phone_number_of_fallback_shifter()

            try:
                log.info('Calling {}'.format(phone_number))
                self.notify(phone_number, msg)
            except:
                log.exception(
                    'Could not notifiy recipient {}'.format(phone_number))
