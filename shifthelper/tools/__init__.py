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


def get_alerts():
    @retry(stop_max_delay=30000,  # 30 seconds max
           wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
           wait_exponential_max=1000,  # but wait 1 second per try maximum
           wrap_exception=True
           )
    def retry_fetch_fail_after_30sec():
        alerts = requests.get(config['webservice']['post-url'])
        return alerts.json()
    try:
        return retry_fetch_fail_after_30sec()
    except RetryError:
        return {}


def create_db_connection(db_config=None):
    with lock:
        if db_config is None:
            db_config = config['cloned_db']

        frozen_config = frozenset(db_config.items())

        if frozen_config not in db_engines:
            schema = "mysql+pymysql://{user}:{pw}@{host}:{port}/{db}".format(
                    user=db_config['user'],
                    pw=db_config['password'],
                    host=db_config['host'],
                    db=db_config['database'],
                    port=db_config.get('port', 3306)
                )
            db_engines[frozen_config] = sqlalchemy.create_engine(
                schema,
                pool_recycle=3600,
                connect_args={'ssl': {'ssl-mode': 'preferred'}},
            )
    return db_engines[frozenset(db_config.items())]


def get_last_parking_checklist_entry():
    try:
        db = create_db_connection(config['cloned_db'])
        with db.connect() as conn:
            table = pd.read_sql_query(
                'select * from park_checklist_filled',
                conn
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
        return requests.get(config['webservice']['i_am_awake_url']).json()

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
        return requests.get(config['webservice']['dummy_alerts_url']).json()

    try:
        return retry_fetch_fail_after_30sec()
    except RetryError:
        return {}


def update_heartbeat():
    @retry(
        stop_max_delay=30000,  # 30 seconds max
        wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
        wait_exponential_max=1000,  # but wait 1 second per try maximum
        wrap_exception=True
    )
    def retry_fetch_fail_after_30sec():
        return requests.post(
            config['webservice']['shifthelperHeartbeat'],
            auth=(
                config['webservice']['user'],
                config['webservice']['password']
            )
        ).json()
    try:
        return retry_fetch_fail_after_30sec()
    except RetryError as e:
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
            self.night = current_night
            self.clear()
