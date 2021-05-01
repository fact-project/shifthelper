import os
from datetime import datetime, timedelta
import pandas as pd
from ..tools import config
from ..tools import create_db_connection
from . import TIME_BETWEEN_CLONES
import time
from sqlalchemy import text

import logging
import logging.config


def factdata_MeasurementType():
    return text("""SELECT * from factdata.MeasurementType""")


def calendar_data():
    yesterday_night = (datetime.utcnow() - timedelta(hours=12)).date()
    query = """
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

    return text(query)


def factdata_Schedule():
    return text("""
        SELECT *
        FROM factdata.Schedule AS S
        WHERE
            S.fStart > "{one_month_ago}"
    """.format(one_month_ago=(datetime.utcnow() - timedelta(days=30))))


def users():
    return text("""
        SELECT * from logbook.users
        JOIN
            logbook.userfields
        ON
            logbook.users.uid=logbook.userfields.ufid
        """)

query_funcs = [
    factdata_MeasurementType,
    calendar_data,
    factdata_Schedule,
    users,
]


def park_checklist_filled():
    sandbox_db = create_db_connection(config['sandbox_db'])
    query = text('select * from park_checklist_filled')
    with sandbox_db.begin() as con:
        table = pd.read_sql(query, con)
    return table, 'park_checklist_filled'


def atomic_write(table, table_name, db_out):
    # we save the table to a temporary placeholder to make the
    # change atomic
    if table_name == 'calendar_data':
        table.to_sql('t1', db_out, if_exists="replace", index=False)
    else:
        table.to_sql('t1', db_out, if_exists="replace")

    with db_out.begin() as conn:
        conn.execute(text('DROP TABLE IF EXISTS t2'))
        if conn.dialect.has_table(conn, table_name):
            conn.execute(text('RENAME TABLE {t} to t2, t1 to {t}'.format(
                t=table_name)
            ))
        else:
            conn.execute(text('RENAME TABLE t1 to {t}'.format(t=table_name)))


def do_clone(engine_in, engine_out, log):
    log.info("cloning ...")

    for query_func in query_funcs:
        table_name = query_func.__name__

        with engine_in.connect() as conn:
            table = pd.read_sql_query(query_func(), conn)

        atomic_write(table, table_name, engine_out)

    table, name = park_checklist_filled()
    atomic_write(table, name, engine_out)

    log.info("...done")


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

    engine_in = create_db_connection(config["database"])
    engine_out = create_db_connection(config["cloned_db"])

    time_for_next_clone = datetime.utcnow()
    while True:
        try:
            now = datetime.utcnow()
            if time_for_next_clone <= now:
                time_for_next_clone += TIME_BETWEEN_CLONES
                do_clone(engine_in, engine_out, log)
        except (SystemExit, KeyboardInterrupt):
            break
        except:
            log.exception("error")
        time.sleep(10)  # 10 seconds

if __name__ == '__main__':
    main()
