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


query_funcs = [
    factdata_MeasurementType,
    calendar_data,
    factdata_Schedule,
    users,
]


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

            for query_func in query_funcs:
                table_name = query_func.__name__

                with db_in.connect() as conn:
                    table = pd.read_sql_query(query_func(), conn)
                # we save the table to a temporary placeholder to make the
                # change atomic
                if table_name == 'calendar_data':
                    table.to_sql('t1', db_out, if_exists="replace", index=False)
                else:
                    table.to_sql('t1', db_out, if_exists="replace")
                db_out.execute('DROP TABLE IF EXISTS t2')
                if db_out.dialect.has_table(db_out, table_name):
                    db_out.execute('RENAME TABLE {t} to t2, t1 to {t}'.format(
                        t=table_name)
                    )
                else:
                    db_out.execute('RENAME TABLE t1 to {t}'.format(t=table_name))

            log.info("...done")
            time.sleep(5 * 60)  # 5 minutes
        except (SystemExit, KeyboardInterrupt):
            break
        except:
            log.exception("error")

if __name__ == '__main__':
    main()
