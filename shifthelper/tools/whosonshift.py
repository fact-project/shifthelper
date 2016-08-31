import pandas as pd
from .. import tools
from functools import lru_cache
from datetime import datetime
from datetime import timedelta

def whoisonshift(clear_cache=False):
    if clear_cache:
        retrieve_calendar_entries.cache_clear()
        retrieve_valid_usernames_from_logbook.cache_clear()

    full_shifter_info = retrieve_shifters_from_calendar()
    only_interesting_stuff = full_shifter_info[["phone_mobile", "telegram_json", "skype", "username", "email"]]
    return only_interesting_stuff

def retrieve_shifters_from_calendar(
        time=None, 
        db=None,
        ):
    if time is None:
        time = datetime.utcnow()

    time = time.replace(minute=0, second=0, microsecond=0)

    calendar_entries = retrieve_calendar_entries(time)
    calendar_entries["username"] = calendar_entries["u"]

    all_shifters = retrieve_valid_usernames_from_logbook()
    tonights_shifters = pd.merge(all_shifters, calendar_entries, how='inner', on="username")

    return tonights_shifters

@lru_cache(100)
def retrieve_calendar_entries(dt_date, db=None):
    if db is None:
        db = tools.create_db_connection()

    yesterday_night = (dt_date - timedelta(hours=12)).date()

    query = "SELECT u from calendar.Data where y={y} and m={m} and d={d}".format(
                y=yesterday_night.year, 
                m=yesterday_night.month - 1,
                d=yesterday_night.day
            )
    return pd.read_sql_query(query, db)

@lru_cache(1)
def retrieve_valid_usernames_from_logbook(db=None):
    if db is None:
        db = tools.create_db_connection()

    memberlist = pd.read_sql_query((
        "SELECT * from logbook.users "
        "JOIN logbook.userfields "
        "ON logbook.users.uid=logbook.userfields.ufid"), db)

    memberlist = memberlist.rename(columns={
            "fid1": "institute",
            "fid3": "gender",
            "fid4": "phone_office",
            "fid5": "phone_mobile",
            "fid6": "telegram_json",
            "fid7": "skype",
            "fid8": "contact_blob",
        })

    return memberlist
