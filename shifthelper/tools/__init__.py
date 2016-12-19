import os
import threading
import sqlalchemy
import json
import pandas as pd
import requests
from retrying import retry, RetryError
from fact import night_integer
from datetime import datetime
from collections import defaultdict

__all__ = ['create_db_connection', 'config']


configfile = os.environ.get(
    'SHIFTHELPER_CONFIG',
    os.path.join(os.environ['HOME'], '.shifthelper', 'config.json')
)

with open(configfile) as f:
    config = json.load(f)


lock = threading.Lock()

db_engines = {}


@retry(stop_max_delay=30000,  # 30 seconds max
       wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
       wait_exponential_max=1000,  # but wait 1 second per try maximum
       )
def get_alerts():
    alerts = requests.get(config['webservice']['post-url'])
    return alerts.json()


def create_db_connection(db_config=None):
    with lock:
        if db_config is None:
            db_config = config['database']

        if not frozenset(db_config.items()) in db_engines:
            db_engines[frozenset(db_config.items())] = sqlalchemy.create_engine(
                "mysql+pymysql://{user}:{pw}@{host}:{port}/{db}".format(
                    user=db_config['user'],
                    pw=db_config['password'],
                    host=db_config['host'],
                    db=db_config['database'],
                    port=db_config.get('port', 3306)
                )
            )
    return db_engines[frozenset(db_config.items())]


def get_last_parking_checklist_entry():
    try:
        table = pd.read_sql_query(
            'select * from park_checklist_filled',
            create_db_connection(config['sandbox_db'])
            )
        return table.sort_values('created').iloc[-1].created
    except IndexError:
        # In case we can not find out when the checklist was filled
        # we pretend it was only filled waaaay in the future.
        # In all checks, which check if it was *already* filled
        # this future timestamp will result as False
        return datetime.max


def fetch_users_awake():
    @retry(
        stop_max_delay=30000,  # 30 seconds max
        wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
        wait_exponential_max=1000,  # but wait 1 second per try maximum
        wrap_exception=True
    )
    def retry_fetch_fail_after_30sec():
        return requests.get('http://webinterface/iAmAwake').json()

    try:
        return retry_fetch_fail_after_30sec()
    except RetryError:
        return {}


def fetch_dummy_alerts():
    @retry(
        stop_max_delay=30000,  # 30 seconds max
        wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
        wait_exponential_max=1000,  # but wait 1 second per try maximum
        wrap_exception=True
    )
    def retry_fetch_fail_after_30sec():
        return requests.get('http://webinterface/dummyAlert').json()

    try:
        return retry_fetch_fail_after_30sec()
    except RetryError:
        return {}


class NightlyResettingDefaultdict(defaultdict):
    def __init__(self, *args, **kwargs):
        self.night = night_integer(datetime.utcnow())
        super().__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        self.reset_if_night_change()
        super().__setitem__(key, value)

    def __getitem__(self, key):
        self.reset_if_night_change()
        return super().__getitem__(key)

    def reset_if_night_change(self):
        current_night = night_integer(datetime.utcnow())
        if current_night != self.night:
            self.clear()
