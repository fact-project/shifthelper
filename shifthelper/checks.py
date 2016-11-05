import logging
from operator import attrgetter
from datetime import datetime, timedelta
import requests
from requests.exceptions import RequestException
from retrying import retry
import pandas as pd

from custos import IntervalCheck

from custos import levels, Message
from .tools import config

log = logging.getLogger(__name__)

class FactIntervalCheck(IntervalCheck):
    def __init__(self, name, checklist, category, interval=300):
        self.name = name
        self.checklist = checklist
        self.category = category
        super().__init__(interval=interval)

    def check(self):
        if all([f() for f in self.checklist]):
            self.message(self.checklist)

    def message(self, checklist, **kwargs):
        self.queue.put(Message(
            text=' and \n'.join(map(attrgetter('__doc__'), checklist)),
            level=message_level(self.__class__.__name__),
            check=self.name,
            category=self.category,
            ))

@retry(stop_max_delay=30000,  # 30 seconds max
       wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
       wait_exponential_max=1000,  # but wait 1 second per try maximum
       )

def message_level(checkname):
    '''
    return the message severity level for a certain check,
    based on whether all the alerts have been acknowledged or not
    '''
    if all_recent_alerts_acknowledged(checkname):
        return levels.INFO
    else:
        return levels.WARNING

def all_recent_alerts_acknowledged(checkname):
    '''
    have a look at shifthelper webinterface page and see if the
    user has already acknowledged all the alerts from the given
    checkname.

    In case we cannot even reach the webinterface, we have to assume the
    user also cannot reach the website, so nothing will be acknowledged.
    So in that case we simply return False as well
    '''
    try:
        all_alerts = requests.get(config['webservice']['post-url']).json()
    except RequestException:
        log.warning('Could not check acknowledged alerts')
        return False

    if not all_alerts:
        return False

    now = datetime.utcnow()
    all_alerts = pd.DataFrame(all_alerts)
    all_alerts['timestamp'] = pd.to_datetime(all_alerts.timestamp, utc=True)

    my_alerts = all_alerts[all_alerts.check == checkname]
    if my_alerts.empty:
        return False

    my_recent_alerts = my_alerts[(now - my_alerts.timestamp) < timedelta(minutes=10)]
    if my_recent_alerts.empty:
        return False

    if not my_recent_alerts.acknowledged.all():
        return False
    return True

