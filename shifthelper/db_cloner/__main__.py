from datetime import datetime, timedelta
import pandas as pd
from ..tools import config
from ..tools import create_db_connection
import time


def factdata_MeasurementType():
    return """SELECT * from factdata.MeasurementType"""
        
def calendar_data():
    yesterday_night = (datetime.utcnow() - timedelta(hours=12)).date()
    return """
        SELECT * 
        FROM calendar.Data 
        WHERE y={y} 
            AND m={m} 
            AND d={d}
        """.format(
                y=yesterday_night.year, 
                m=yesterday_night.month - 1,
                d=yesterday_night.day
            )

def factdata_Schedule():
    return """
        SELECT * 
        FROM factdata.Schedule AS S 
        WHERE
            S.fStart > "{one_month_ago}"
    """.format(one_month_ago = (datetime.utcnow() - timedelta(days=30)))
    

def users():
    return """
        SELECT * from logbook.users 
        JOIN 
            logbook.userfields 
        ON 
            logbook.users.uid=logbook.userfields.ufid
        """


def main():
    db_in = create_db_connection(config["database"])
    db_out = create_db_connection(config["cloned_db"])

    while True:
        print(time.asctime(), "clonging ...")
        for query_func in [factdata_MeasurementType, calendar_data, factdata_Schedule, users]:
            table = pd.read_sql_query(query_func(), db_in)
            table.to_sql(query_func.__name__, db_out, if_exists="replace")
        print(time.asctime(), "...done")
        time.sleep(15 * 60) # 15 minutes