import pandas as pd
from .. import tools
from functools import lru_cache
from datetime import datetime
from datetime import timedelta

import logging

log = logging.getLogger(__name__)


calendar_query = '''
SELECT u
FROM calendar_data
WHERE
    y={y}
    AND m={m}
    AND d={d}
    AND NOT x
;
'''


def get_current_shifter(clear_cache=False):
    if clear_cache:
        retrieve_calendar_entries.cache_clear()
        retrieve_valid_usernames_from_logbook.cache_clear()

    full_shifter_info = retrieve_shifters_from_calendar()
    only_interesting_stuff = full_shifter_info[
        ["phone_mobile", "telegram_id", "skype", "username", "email"]
    ]
    shifter = only_interesting_stuff.iloc[0]
    log.debug('Found shifter {}'.format(shifter.username))
    return shifter


def retrieve_shifters_from_calendar(
        time=None,
        db=None,
        ):
    if time is None:
        time = datetime.utcnow()

    time = time.replace(second=0, microsecond=0)

    calendar_entries = retrieve_calendar_entries(time)
    calendar_entries["username"] = calendar_entries["u"]

    all_shifters = retrieve_valid_usernames_from_logbook()
    tonights_shifters = pd.merge(
        all_shifters, calendar_entries,
        how='inner', on="username"
    )

    return tonights_shifters


@lru_cache(100)
def retrieve_calendar_entries(dt_date, db=None):
    if db is None:
        db = tools.create_db_connection(tools.config['cloned_db'])

    yesterday_night = (dt_date - timedelta(hours=12)).date()

    query = calendar_query.format(
        y=yesterday_night.year,
        m=yesterday_night.month - 1,
        d=yesterday_night.day
    )
    return pd.read_sql_query(query, db)


@lru_cache(1)
def retrieve_valid_usernames_from_logbook(db=None):
    if db is None:
        db = tools.create_db_connection(tools.config['cloned_db'])

    memberlist = pd.read_sql_query("SELECT * from users", db)
    memberlist = memberlist.rename(columns={
            "fid1": "institute",
            "fid3": "gender",
            "fid4": "phone_office",
            "fid5": "phone_mobile",
            "fid6": "comment",
            "fid7": "skype",
            "fid8": "contact_blob",
            "fid9": "telegram_id",
        })

    return memberlist
