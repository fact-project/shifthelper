import os
import sqlalchemy
import json

with open(os.path.join(os.environ['HOME'], '.shifthelper', 'config.json')) as f:
    config = json.load(f)

def create_db_connection():
    db_config = config['database']
    factdb = sqlalchemy.create_engine(
        "mysql+pymysql://{user}:{pw}@{host}/{db}".format(
            user = db_config['user'],
            pw = db_config['password'],
            host = db_config['host'],
            db = db_config['database'],
        )
    )
    return factdb
