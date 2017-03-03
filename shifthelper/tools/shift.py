import pandas as pd
from .. import tools
from functools import lru_cache
from datetime import datetime
from datetime import timedelta
from cachetools import TTLCache, cached

import logging

log = logging.getLogger(__name__)


def get_current_shifter(clear_cache=False, db=None):
    if clear_cache:
        retrieve_calendar_entries.cache_clear()
        retrieve_valid_usernames_from_logbook.cache_clear()

    full_shifter_info = retrieve_shifters_from_calendar(db=db)
    only_interesting_stuff = full_shifter_info[
        ["phone_mobile", "telegram_id", "username", "rolename"]
    ]
    log.debug('Found these shifters: {}'.format(only_interesting_stuff))
    return only_interesting_stuff


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
        left=all_shifters,
        right=calendar_entries,
        left_on='uid',
        right_on='user_id',
        how='inner',

    )

    return tonights_shifters


@lru_cache(100)
def retrieve_calendar_entries(dt_date, db=None):
    if db is None:
        db = tools.create_db_connection(tools.config['cloned_db'])

    roles = pd.read_sql_query(
        """SELECT
            id as role_id,
            name as rolename
        FROM sandbox_role
        """,
        db
    )

    calendarentries = pd.read_sql_query(
        """SELECT *
        FROM sandbox_calendarentry
        WHERE
            start<'{now}'
            AND end>'{now}'
        """.format(
            now=dt_date.strftime('%Y-%m-%d %H:%M:%S'),
        ),
        db
    )

    result = pd.merge(
        left=calendarentries,
        right=roles,
        on='role_id',
        how='inner',
    )

    return result


# cache user data only for ten minutes, so changes take effect eventually
@cached(cache=TTLCache(1, ttl=10 * 60))
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

NORMAL_SHIFTERS = ['Starter', 'Shifter', 'Parker', 'Shifter_Awake']
FALLBACK_SHIFTERS = ['Fallback_Shifter']
FLARE_EXPERS = ['Flare_Expert',]
FALLBACK_FLARE_EXPERS = ['Fallback_Flare_Expert',]

def get_shifter_of_category(category, next_level):
    shifters = get_current_shifter()
    shifters = shifters[shifters.rolename.isin(category)]
    if len(shifters) == 0:
        log.warn(
            'Found no shifters of category: {0:%r}'.format(category)
        )
        return next_level()
    else:
        if len(shifters) > 1:
            log.warn(
                'found {} shifters. Choosing a random shifter'.format(
                    len(shifters)
                )
            )
        return shifters.iloc[0]

def normal_shifter():
    return get_shifter_of_category(
        NORMAL_SHIFTERS,
        fallback_shifter
    )

def fallback_shifter():
    return get_shifter_of_category(
        FALLBACK_SHIFTERS,
        developer
    )

def developer():
    return config['developer']['phone_number']
    return [config['developer']['telegram_id']]
