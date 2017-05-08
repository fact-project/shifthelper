import requests
from retrying import retry, RetryError
import datetime
from .tools.shift import get_current_shifter
from copy import copy
from .categories import CATEGORY_DEVELOPER
from .tools import config
from cachetools import cached, TTLCache

import logging
log = logging.getLogger(__name__)


class NotAcknowledgedMessagePseudoNotifier:
    """
    Pseudo-Notifier, using the custos.Notifier API to keep track of what
    messages have been issued to the outside world.

    By checking the "acknowledge" status of alerts on the website
    it can provide `recipients` functions for other real Notifiers, like e.g.
    the custos.TwilioNotifier.
    """

    def __init__(self,
                 time_before_fallback=datetime.timedelta(minutes=15),
                 max_time_for_fallback=datetime.timedelta(minutes=15),
                 ):
        self.time_before_fallback = time_before_fallback
        self.max_time_for_fallback = max_time_for_fallback
        self.handled_messages = []

    def handle_message(self, msg):
        self.handled_messages.append(msg)

    def recipients_phone_numbers(self, msg_category):
        self._remove_acknowledged_and_old_calls()
        numbers_to_call = []

        if msg_category in ('check_error', CATEGORY_DEVELOPER):
            log.debug(
                'Message has category "check_error" or "{}"'.format(
                    CATEGORY_DEVELOPER)
                )
            numbers_to_call.append(self.phone_number_of_developer())

        else:
            log.debug('Getting phone number of primary shifter')
            numbers_to_call.append(self.phone_number_of_normal_shifter())

            if self._get_oldest_call_age() >= self.time_before_fallback:
                log.debug('Getting phone number of fallback shifter')
                numbers_to_call.append(self.phone_number_of_fallback_shifter())

        return numbers_to_call

    def _remove_acknowledged_and_old_calls(self):
        """ from the list of not acknowledged calls
        remove all calls:
         * which have been acknowledged on the web page
         * which are old
        """
        for msg in copy(self.handled_messages):
            age = datetime.datetime.utcnow() - msg.timestamp
            if age > (self.max_time_for_fallback + self.time_before_fallback):
                self.handled_messages.remove(msg)

            if is_alert_acknowledged(msg.uuid):
                self.handled_messages.remove(msg)

    def _get_oldest_call_age(self):
        max_age = datetime.timedelta()
        for msg in self.handled_messages:
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


@retry(stop_max_delay=30000,  # 30 seconds max
       wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
       wait_exponential_max=1000,  # but wait 1 second per try maximum
       wrap_exception=True,
       )
@cached(cache=TTLCache(1, ttl=30))
def get_alerts():
    return requests.get(config['webservice']['post-url']).json()


def is_alert_acknowledged(self, uuid):
    try:
        alerts = get_alerts()
        return alerts[uuid]['acknowledged']
    except (IndexError, TypeError, RetryError):
        return False

