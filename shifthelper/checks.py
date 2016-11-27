import logging
import requests
import pandas as pd
import numpy as np
from operator import attrgetter
from datetime import datetime, timedelta
from requests.exceptions import RequestException
from retrying import retry
from io import BytesIO
from collections import defaultdict

from custos import IntervalCheck
from custos import levels

from .tools import config, create_db_connection, NightlyResettingDefaultdict
from fact.qla import get_qla_data, bin_qla_data, plot_qla
from fact import night_integer

log = logging.getLogger(__name__)

database = create_db_connection()


ALERT_SIGNIFICANCE = 3
# for all sources but the mrks and crab the alert rate is 15 Evts / h
FLARE_ALERT_LIMITS = defaultdict(lambda: 15.0)
FLARE_ALERT_LIMITS['Mrk 501'] = 50.0
FLARE_ALERT_LIMITS['Mrk 421'] = 50.0
# we won't issue flare alerts for crab without thorough investigation
FLARE_ALERT_LIMITS['Crab'] = np.inf
nightly_max_rate = NightlyResettingDefaultdict(lambda: -np.inf)


class FactIntervalCheck(IntervalCheck):
    def __init__(self, name, checklist, category, interval=300):
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


class FlareAlertCheck(IntervalCheck):
    def __init__(self, category, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category

    def check(self):
        unbinned_qla_data = retry_get_qla_data_fail_after_30sec()

        if unbinned_qla_data is None:
            self.log.debug('No qla data available yet')
            return
        if len(unbinned_qla_data) == 0:
            self.log.debug('No qla data available yet')
            return

        qla_data = bin_qla_data(unbinned_qla_data, bin_width_minutes=20)
        qla_max_rates = get_max_rate_and_significance(qla_data)
        for source, data in qla_max_rates.iterrows():
            self.log.debug(
                'Source {} has max rate of {:.1f} Evts/h with {:.1f} sigma'.format(
                    source, data['rate'], data['significance']
                )
            )

        significant_qla_max_rates = get_max_rate_and_significance(
            qla_data[qla_data.significance >= ALERT_SIGNIFICANCE]
        )

        # create the image, send it only once if multiple sources flare
        image_file = None
        image_send = False

        for source, data in significant_qla_max_rates.iterrows():
            if (data['rate'] > FLARE_ALERT_LIMITS[source] and
                    data['rate'] > nightly_max_rate[source]):

                nightly_max_rate[source] = data['rate']

                if image_file is None:
                    image_file = BytesIO()
                    plot_qla(qla_data, image_file)
                    image_file.seek(0)

                self.message(
                    'Source {} above flare alert limit with '
                    '{:.1f} Evts/h and {:.1f} sigma! '
                    'Please call the Flare Expert'.format(
                        source, data['rate'], data['significance'],
                    ),
                    category=self.category,
                    level=message_level(self.name),
                    image=None if image_send else image_file,
                )
                image_send = True

@retry(
        stop_max_delay=30000,  # 30 seconds max
        wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
        wait_exponential_max=1000,  # but wait 1 second per try maximum
        )
def retry_get_qla_data_fail_after_30sec():
    return get_qla_data(night_integer(datetime.utcnow()), database)


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


def get_max_rate_and_significance(qla_data):
    idx = qla_data.groupby('fSourceName')['rate'].idxmax()
    qla_max_rates = qla_data[['fSourceName', 'rate', 'significance']].loc[idx]
    return qla_max_rates.set_index('fSourceName')
