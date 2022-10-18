import os
from datetime import datetime, timedelta, timezone
import time
from sqlalchemy import text

import logging
import logging.config

from .sql import copy_table
from ..tools import config
from ..tools import create_db_connection
from . import TIME_BETWEEN_CLONES


def build_calendar_select(night=None):
    if night is None:
        # current "night", so before 12:00 am, we get the date of yesterday
        night = (datetime.now(timezone.utc) - timedelta(hours=12)).date()

    # See https://developer.mozilla.org/de/docs/Web/JavaScript/Reference/Global_Objects/Date/getMonth
    # and https://www.destroyallsoftware.com/talks/wat
    return text(f'''
    SELECT *
    FROM `Data`
    WHERE y={night.year} AND m={night.month - 1} and d={night.day}
    ''')


def build_schedule_select(since=None):
    if since is None:
        since = datetime.now(timezone.utc) - timedelta(days=30)

    return text(f"""
        SELECT *
        FROM factdata.Schedule AS S
        WHERE
            S.fStart > "{since}"
    """)


def do_clone(engines, log):
    t0 = time.perf_counter()
    log.info("cloning ...")

    copy_table(engines['factdata'], engines['cloned'], 'MeasurementType')

    select_query = build_schedule_select()
    copy_table(engines['factdata'], engines['cloned'], 'Schedule', select_query=select_query)

    select_query = build_calendar_select()
    copy_table(
        engines['calendar'], engines['cloned'], 'Data',
        output_table='calendar_data', select_query=select_query,
    )

    copy_table(engines['logbook'], engines['cloned'], 'users')
    copy_table(engines['logbook'], engines['cloned'], 'userfields')

    copy_table(engines['sandbox'], engines['cloned'], 'park_checklist_filled')
    log.info(f"...done in {time.perf_counter() - t0:.2} s")


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

    engines = {}
    engines['factdata'] = create_db_connection(config["database"], database='factdata')
    engines['logbook'] = create_db_connection(config["database"], database='logbook')
    engines['calendar'] = create_db_connection(config["database"], database='calendar')
    engines['sandbox'] = create_db_connection(config["database"], database='sandbox')
    engines['cloned'] = create_db_connection(config["cloned_db"])

    time_for_next_clone = datetime.utcnow()
    while True:
        try:
            now = datetime.utcnow()

            if time_for_next_clone <= now:
                time_for_next_clone += TIME_BETWEEN_CLONES
                do_clone(engines, log)

            time.sleep(10)  # 10 seconds
        except (SystemExit, KeyboardInterrupt):
            break
        except:
            log.exception("error")

if __name__ == '__main__':
    main()
