import os
import threading
import sqlalchemy
import json

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
