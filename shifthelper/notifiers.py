import datetime
import requests

from custos import TwilioNotifier
from .tools.shift import get_current_shifter
from copy import copy
from .tools import config, get_alerts
from .categories import CATEGORY_DEVELOPER

import logging
log = logging.getLogger(__name__)


class FactTwilioNotifier(TwilioNotifier):
    def __init__(self,
                 time_before_fallback=datetime.timedelta(minutes=15),
                 max_time_for_fallback=datetime.timedelta(minutes=15),
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.time_before_fallback = time_before_fallback
        self.max_time_for_fallback = max_time_for_fallback
        self.not_acknowledged_calls = []
        self.nobody_is_listening = False
        self.twiml = 'hangup'

        # actual recipients are determinded in
        # handle_message() using phone_number_of...()
        kwargs["recipients"] = []

    def notify(self, recipient, msg):
        super().notify(recipient, msg)
        self.not_acknowledged_calls.append((self.call, msg))

    def _remove_acknowledged_and_old_calls(self):
        """ from the list of not acknowledged calls
        remove all calls, which have been acknowledged on the web page

        Also remove calls older than 2 hours, to get out of
        a "call the backup shifter" dead lock
        """
        try:
            alerts = {a['uuid']: a for a in get_alerts()}
        except requests.exceptions.RequestException:
            return

        for call, msg in copy(self.not_acknowledged_calls):
            age = datetime.datetime.utcnow() - msg.timestamp
            if age > self.max_time_for_fallback:
                self.not_acknowledged_calls.remove((call, msg))
            else:
                try:
                    alert = alerts[msg.uuid]
                except KeyError:
                    continue

                if alert['acknowledged'] is True:
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
            phone_number = get_current_shifter().phone_mobile
            if not phone_number:
                return self.phone_number_of_fallback_shifter()
            return phone_number
        except:
            log.exception('Error getting phone number, calling developer')
            return self.phone_number_of_developer()


    def phone_number_of_fallback_shifter(self):
        return config['fallback_shifter']['phone_number']


    def phone_number_of_developer(self):
        return config['developer']['phone_number']


    def get_numbers_to_call(self, msg):
        numbers_to_call = []
        if msg.category in ('check_error', CATEGORY_DEVELOPER):
            log.debug('Message has category "check_error"')
            numbers_to_call.append(self.phone_number_of_developer())

        else:
            if self._get_oldest_call_age() < self.time_before_fallback:
                log.debug('Getting phone number of primary shifter')
                numbers_to_call.append(self.phone_number_of_normal_shifter())

            else:
                log.debug('Getting phone number of fallback shifter')
                numbers_to_call.append(self.phone_number_of_fallback_shifter())
        return numbers_to_call


    def handle_message(self, msg):
        self._remove_acknowledged_and_old_calls()
        log.debug('Got a message')
        if msg.level >= self.level:
            log.debug('Message is over alert level')

            numbers_to_call = self.get_numbers_to_call(msg)
            for phone_number in numbers_to_call:
                try:
                    log.info('Calling {}'.format(phone_number))
                    self.notify(phone_number, msg)
                except:
                    log.exception(
                        'Could not notifiy recipient {}'.format(phone_number))
