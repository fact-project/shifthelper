import logging
import numpy as np
from operator import attrgetter
from datetime import datetime, timedelta
from retrying import retry
from io import BytesIO
from collections import defaultdict

from custos import IntervalCheck
from custos import levels

from .tools import create_db_connection, NightlyResettingDefaultdict
from fact.qla import get_qla_data, bin_qla_data, plot_qla
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


class ExponentialTimedActor:
    def __init__(self,
                 action,
                 minimum_pause=timedelta(minutes=1),
                 maximum_pause=timedelta(minutes=10),
                 multiplicator=2,
                 ):
        self.maximum_pause = maximum_pause
        self.minimum_pause = minimum_pause
        self.multiplicator = multiplicator

        self.action = action
        self.reset()

    @property
    def _is_time_for_action(self):
        if self.last_action is None:
            return True
        return datetime.utcnow() - self.last_action > self.pause

    def _update(self):
        self.last_action = datetime.utcnow()
        self.pause *= self.multiplicator
        if self.pause > self.maximum_pause:
            self.pause = self.maximum_pause
        if self.pause < self.minimum_pause:
            self.pause = self.minimum_pause

    def reset(self):
        self.last_action = None
        self.pause = self.minimum_pause

    def __call__(self, *args, **kwargs):
        if self._is_time_for_action:
            self._update()
            self.action(*args, **kwargs)


class FactIntervalCheck(IntervalCheck):
    def __init__(self, name, checklist, category, interval=120):
        super().__init__(interval=interval, name=name)
        self.checklist = checklist
        self.category = category
        self.send_msg = ExponentialTimedActor(action=self.message_from_docs)

    def check(self):
        if all([f() for f in self.checklist]):
            self.send_msg(self.checklist)
        else:
            self.send_msg.reset()

    def message_from_docs(self, checklist, **kwargs):
        self.message(
            text=' and \n'.join(map(attrgetter('__doc__'), checklist)),
            level=levels.WARNING,
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
                    level=levels.WARNING,
                    image=None if image_send else image_file,
                )
                image_send = True


@retry(
        stop_max_delay=30000,  # 30 seconds max
        wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
        wait_exponential_max=1000,  # but wait 1 second per try maximum
        )
def retry_get_qla_data_fail_after_30sec(database=None):
    database = database or create_db_connection()
    return get_qla_data(night_integer(datetime.utcnow()), database)


def get_max_rate_and_significance(qla_data):
    idx = qla_data.groupby('fSourceName')['rate'].idxmax()
    qla_max_rates = qla_data[['fSourceName', 'rate', 'significance']].loc[idx]
    return qla_max_rates.set_index('fSourceName')
