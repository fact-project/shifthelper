import os
import threading
from sqlalchemy import create_engine, text
import json
import pandas as pd
import requests
from retrying import retry, RetryError
from datetime import datetime, timezone

__all__ = ['create_db_connection', 'config']


configfile = os.environ.get(
    'SHIFTHELPER_CONFIG',
    os.path.join(os.environ['HOME'], '.shifthelper', 'config.json')
)

with open(configfile) as f:
    config = json.load(f)


lock = threading.Lock()

db_engines = {}


def local_isoformat_to_datetime(s, tzinfo=timezone.utc):
    return datetime.fromisoformat(s).replace(tzinfo=tzinfo)


def get_alerts():
    @retry(stop_max_delay=30000,  # 30 seconds max
           wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
           wait_exponential_max=1000,  # but wait 1 second per try maximum
           wrap_exception=True
           )
    def retry_fetch_fail_after_30sec():
        ret = requests.get(config['webservice']['post-url'])
        ret.raise_for_status()

        # parse times
        alerts = ret.json()
        for alert in alerts:
            alert["timestamp"] = local_isoformat_to_datetime(alert["timestamp"])

        return alerts

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
            db_engines[frozen_config] = create_engine(
                schema,
                pool_recycle=3600,
                connect_args={'ssl': {'ssl-mode': 'preferred'}},
                future=True,
            )
    return db_engines[frozenset(db_config.items())]



checklist_query = text('''
SELECT created
FROM park_checklist_filled
ORDER BY created DESC
LIMIT 1
''')


def get_last_parking_checklist_entry():
    engine = create_db_connection()
    with engine.begin() as conn:
        result = conn.execute(checklist_query)
        row = result.first()

    if row is None:
        # In case we can not find out when the checklist was filled
        # we pretend it was only filled waaaay in the future.
        # In all checks, which check if it was *already* filled
        # this future timestamp will result as False
        return datetime.max.replace(tzinfo=timezone.utc)
    else:
        return row._mapping['created'].replace(tzinfo=timezone.utc)


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
    except RetryError:
        return {}
