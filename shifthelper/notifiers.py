import datetime
import requests

from custos import TwilioNotifier
from .tools.shift import get_current_shifter
from .tools import shift
from copy import copy
from .tools import config, get_alerts
from .categories import CATEGORY_DEVELOPER

import logging
log = logging.getLogger(__name__)

class UnAcknowledgedMessages:
    """
    list like. collection of custos.Message
    that can find out which messages were not acknowledged on
    the shifthelper_webinterface.

    Can find out, how old the oldest message is, which was not
    yet ack'ed.
    """
    def __init__(self, age_limit):
        self.messages = []
        self.age_limit = age_limit

    def append(self, msg):
        """ append a new message to the list
        """
        self.messages.append(msg)

    def oldest_age(self):
        """ return max(age) of messages, that were not acknowledged.
        """
        # when ever we need this info, we simply do this kind of "update"
        self._remove_old_messages()
        self._remove_acknowledged_messages()

        return max(
            datetime.datetime.utcnow() - msg.timestamp for msg in self.messages
        )

    def _remove_old_messages(self):
        self.messages = [msg for msg in self.messages if
            datetime.datetime.utcnow() - msg.timestamp <= self.age_limit
        ]

    def _remove_acknowledged_messages(self):
        self.messages = [
            msg for msg in self.messages if
                self._alerts().get(msg.uuid, False) is False
        ]

    def _alerts(self):
        try:
            alerts = {a['uuid']: a for a in get_alerts()}
        except requests.exceptions.RequestException:
            return {}


class FactNotifierMixin:
    """ Mixin for FACT Notifiers.


    provides `people_to_inform()` method, which is needed by
    explicit Notifiers to generate `recipients`.

    Takes care of tracking the age of unacknowledged messages,
    in order to implement `people_to_inform`

    overwrites custos.Notifier.notify in order to keep track of
    old messages.
    """

    def __init__(self,
                 time_before_fallback=datetime.timedelta(minutes=15),
                 max_time_for_fallback=datetime.timedelta(minutes=15),
                 *args,
                 **kwargs):

        kwargs["recipients"] = None  # set to make __init__ work;
        super().__init__(*args, **kwargs)

        self.time_before_fallback = time_before_fallback
        self.max_time_for_fallback = max_time_for_fallback
        self.unacknowledged_messages = UnAcknowledgedMessages(
            age_limit=self.max_time_for_fallback + self.time_before_fallback
        )

    def notify(self, recipient, msg):
        super().notify(recipient, msg)
        self.unacknowledged_messages.append(msg)

    def people_to_inform(self, category):
        people = []

        if category not in ('check_error', CATEGORY_DEVELOPER):
            log.debug('Getting shifter')
            people.append(shift.normal_shifter())

            if self.unacknowledged_messages.oldest_age() >= self.time_before_fallback:
                log.debug('shifter does not ack messages; getting fallback')
                people.append(shift.fallback_shifter())
        else:
            log.debug('Message has category "check_error" or "{}"'.format(CATEGORY_DEVELOPER))
            people.append(shift.developer())

        return people

class FactTwilioNotifier(FactNotifierMixin, TwilioNotifier):
    def recipients(self, category):
        return [
            p.phone_mobile for p in self.people_to_inform(category)
        ]

class FactTelegramNotifier(FactNotifierMixin, TelegramNotifier):
    def recipients(self, category):
        return [
            p.telegram_id for p in self.people_to_inform(category)
        ]
