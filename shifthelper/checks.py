import logging
import pandas as pd
import numpy as np
from operator import attrgetter
from datetime import datetime, timedelta
from requests.exceptions import RequestException
from retrying import retry
from collections import defaultdict

from custos import IntervalCheck
from custos import levels

from .tools import create_db_connection, NightlyResettingDefaultdict, get_alerts
from fact import night_integer

log = logging.getLogger(__name__)


ALERT_SIGNIFICANCE = 3
# for all sources but the mrks and crab the alert rate is 15 Evts / h
FLARE_ALERT_LIMITS = defaultdict(lambda: 15.0)
FLARE_ALERT_LIMITS['Mrk 501'] = 60.0
FLARE_ALERT_LIMITS['Mrk 421'] = 60.0
# we won't issue flare alerts for crab without thorough investigation
FLARE_ALERT_LIMITS['Crab'] = np.inf
nightly_max_rate = NightlyResettingDefaultdict(lambda: -np.inf)


class FactIntervalCheck(IntervalCheck):
    def __init__(self, name, checklist, category, interval=120):
        super().__init__(interval=interval, name=name)
        self.checklist = checklist
        self.category = category

    def check(self):
        if all([f() for f in self.checklist]):
            self.message_from_docs(self.checklist)

    def message_from_docs(self, checklist, **kwargs):
        self.message(
            text=' and \n'.join(map(attrgetter('__doc__'), checklist)),
            level=message_level(self.name),
            category=self.category,
        )


@retry(
        stop_max_delay=30000,  # 30 seconds max
        wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
        wait_exponential_max=1000,  # but wait 1 second per try maximum
        )
def retry_get_qla_data_fail_after_30sec(database=None):
    database = database or create_db_connection()
    return get_qla_data(night_integer(datetime.utcnow()), database)


def message_level(checkname, check_time=timedelta(minutes=10), alerts=None):
    '''
    return the message severity level for a certain check,
    based on whether all the alerts have been acknowledged or not

    In case we cannot even reach the webinterface, we have to assume the
    user also cannot reach the website, so nothing will be acknowledged.
    So in that case we simply return the higher level as well.
    '''
    try:
        acknowledged = all_recent_alerts_acknowledged(
            checkname=checkname,
            check_time=check_time,
            alerts=alerts,
            result_if_no_alerts=False,
        )
    except RequestException:
        log.exception('Getting alerts failed')
        acknowledged = False

    if acknowledged:
        return levels.INFO
        log.debug('Giving message status INFO')
    else:
        log.debug('Giving message status WARNING')
        return levels.WARNING


def all_recent_alerts_acknowledged(
        checkname=None,
        check_time=timedelta(minutes=10),
        alerts=None,
        result_if_no_alerts=False,
        ):
    '''
    have a look at shifthelper webinterface page and see if the
    user has already acknowledged all the alerts from the given
    checkname.

    If there are no alerts matching the specified criteria, the result
    is dependent on the `result_if_no_alerts` option, which defaults to `False`
    '''
    now = pd.Timestamp.utcnow()

    if alerts is None:
        alerts = get_alerts()

        if not alerts:
            return result_if_no_alerts

        alerts = pd.DataFrame(alerts)
        alerts['timestamp'] = pd.to_datetime(alerts.timestamp, utc=True)

    if alerts.empty:
        return result_if_no_alerts

    alerts['age'] = now - alerts.timestamp

    if checkname is not None:
        alerts = alerts[alerts.check == checkname]

    if check_time is not None:
        alerts = alerts[alerts.age < check_time]

    if alerts.empty:
        return result_if_no_alerts

    return alerts.acknowledged.all()


def get_max_rate_and_significance(qla_data):
    idx = qla_data.groupby('fSourceName')['rate'].idxmax()
    qla_max_rates = qla_data[['fSourceName', 'rate', 'significance']].loc[idx]
    return qla_max_rates.set_index('fSourceName')
