from datetime import datetime
import pandas as pd
from ..tools import config
from ..tools import create_db_connection

def main():
    db_in = create_db_connection(config["database"])
    db_out = create_db_connection(config["cloned_db"])
    yesterday_night = (datetime.utcnow() - timedelta(hours=12)).date()
    query = "SELECT u from calendar.Data where y={y} and m={m} and d={d}".format(
                    y=yesterday_night.year, 
                    m=yesterday_night.month - 1,
                    d=yesterday_night.day
                )
    calendar_data = pd.read_sql_query(query, db_in)
    calendar_data.to_sql("calendar_data", db_out, if_exists="replace")

