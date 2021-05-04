import logging
from datetime import datetime, timedelta
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from sqlalchemy import text
import pandas as pd

from .. import tools

log = logging.getLogger(__name__)


calendar_query = '''
SELECT u AS username
FROM calendar_data
WHERE
    y={y}
    AND m={m}
    AND d={d}
    AND NOT x
;
'''


shifter_query = '''
SELECT
    u AS username
    fid5 AS phone_mobile
    fid9 AS telegram_id
    email
FROM calendar_data
LEFT JOIN users ON calendar_data.u = users.username
WHERE y=:y AND m=:m AND d=:d AND NOT x
'''


def get_current_shifter(db=None):
    full_shifter_info = retrieve_shifters_from_calendar(db=db)
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

    calendar_entries = retrieve_calendar_entries(time, db=db)

    all_shifters = retrieve_valid_usernames_from_logbook(db=db)
    tonights_shifters = pd.merge(
        all_shifters, calendar_entries,
        how='inner', on="username"
    )

    return tonights_shifters


@cached(
    cache=TTLCache(1, ttl=5 * 60),
    key=lambda dt_date, db: hashkey(dt_date)
)
def retrieve_calendar_entries(dt_date, db=None):
    if db is None:
        db = tools.create_db_connection()

    yesterday_night = (dt_date - timedelta(hours=12)).date()

    query = calendar_query.format(
        y=yesterday_night.year,
        m=yesterday_night.month - 1,
        d=yesterday_night.day
    )

    with db.connect() as conn:
        return pd.read_sql_query(text(query), conn)


@cached(
    cache=TTLCache(1, ttl=5 * 60),
    key=lambda db: hashkey(None)
)
def retrieve_valid_usernames_from_logbook(db=None):
    if db is None:
        db = tools.create_db_connection()

    with db.connect() as conn:
        memberlist = pd.read_sql_query(text("SELECT * from users"), conn)

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
