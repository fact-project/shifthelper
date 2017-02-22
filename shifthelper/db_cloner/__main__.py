import os
from datetime import datetime, timedelta
import pandas as pd
from ..tools import config
from ..tools import create_db_connection
import time

import logging
import logging.config


def factdata_MeasurementType():
    return """SELECT * from factdata.MeasurementType"""

def shiftcalendar_roles_and_user():
    return """
        SELECT
            u.username,
            uf.fid5 as mobile,
            uf.fid9 as telegram,
            r.name as role_name,
            c.start,
            c.end
        FROM sandbox.calendarentry c
            INNER JOIN sandbox.role r
                ON c.role_id = r.id
            INNER JOIN logbook.users u
                ON c.user_id = u.uid
            INNER JOIN logbook.userfields uf
                ON c.user_id = uf.ufid
    """

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
        d=yesterday_night.day)


def factdata_Schedule():
    return """
        SELECT *
        FROM factdata.Schedule AS S
        WHERE
            S.fStart > "{one_month_ago}"
    """.format(one_month_ago=(datetime.utcnow() - timedelta(days=30)))


def users():
    return """
        SELECT * from logbook.users
        JOIN
            logbook.userfields
        ON
            logbook.users.uid=logbook.userfields.ufid
        """


def main():
    log = logging.getLogger()
    log.setLevel('INFO')
    logfile = os.environ.get(
        'SHIFTHELPER_DBCLONER_LOG',
        os.path.join(os.environ['HOME'], '.shifthelper', 'dbcloner.log')
    )
    formatter = logging.Formatter(
        fmt='%(asctime)s|%(name)s|%(levelname)s|%(module)s|%(lineno)d|%(message)s'
    )
    formatter.converter = time.gmtime  # use utc in log
    for handler in (logging.FileHandler(logfile), logging.StreamHandler()):
        handler.level = logging.INFO
        handler.setFormatter(formatter)
        log.addHandler(handler)

    db_in = create_db_connection(config["database"])
    db_out = create_db_connection(config["cloned_db"])

    while True:
        try:
            log.info("cloning ...")
            for query_func in [
                    factdata_MeasurementType,
                    shiftcalendar_roles_and_user,
                    calendar_data,
                    factdata_Schedule,
                    users]:
                table = pd.read_sql_query(query_func(), db_in)
                table.to_sql(query_func.__name__, db_out, if_exists="replace")
            log.info("...done")
            time.sleep(5 * 60)  # 5 minutes
        except (SystemExit, KeyboardInterrupt):
            break
        except:
            log.exception("error")
