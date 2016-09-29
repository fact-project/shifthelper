import os
import sqlalchemy
import json

with open(os.path.join(os.environ['HOME'], '.shifthelper', 'config.json')) as f:
    config = json.load(f)

def create_db_connection(config=None):
    if config is None:
        db_config = config['database']
    else:
        db_config = config
    factdb = sqlalchemy.create_engine(
        "mysql+pymysql://{user}:{pw}@{host}:{port}/{db}".format(
            user = db_config['user'],
            pw = db_config['password'],
            host = db_config['host'],
            db = db_config['database'],
            port = db_config.get('port', 3306)
        )
    )
    return factdb
