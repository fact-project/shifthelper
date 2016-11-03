import os
import datetime
import threading
import sqlalchemy
import json
import pandas as pd

__all__ = ['create_db_connection', 'config']

with open(os.path.join(os.environ['HOME'], '.shifthelper', 'config.json')) as f:
    config = json.load(f)


lock = threading.Lock()

db_engines = {}

def create_db_connection(db_config=None):
    with lock:
        if db_config is None:
            db_config = config['database']

        if not frozenset(db_config.items()) in db_engines:
            db_engines[frozenset(db_config.items())] = sqlalchemy.create_engine(
                "mysql+pymysql://{user}:{pw}@{host}:{port}/{db}".format(
                    user = db_config['user'],
                    pw = db_config['password'],
                    host = db_config['host'],
                    db = db_config['database'],
                    port = db_config.get('port', 3306)
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
        return datetime.datetime.max