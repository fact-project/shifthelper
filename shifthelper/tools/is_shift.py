import pandas as pd
from .. import tools
from datetime import datetime, timezone
from retrying import retry
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from sqlalchemy import text

from ..debug_log_wrapper import log_call_and_result


UTC = timezone.utc


def now_seconds(tz=UTC):
    '''Current time rounded to full seconds, by default with tz UTC'''
    return datetime.now(tz=tz).replace(microsecond=0)


@cached(
    cache=TTLCache(1, ttl=5 * 60),
    key=lambda db: hashkey(None)
)
def get_MeasurementType(db=None):
    if db is None:
        db = tools.create_db_connection()

    with db.connect() as conn:
        df = pd.read_sql_query(text("select * from MeasurementType"), conn)
    df.set_index("fMeasurementTypeName", inplace=True)
    return df


def get_last_startup_or_shutdown(
    current_time_rounded_to_seconds=None,
    db=None
):
    if current_time_rounded_to_seconds is None:
        current_time_rounded_to_seconds = now_seconds()

    if db is None:
        db = tools.create_db_connection()

    types = get_MeasurementType(db)
    query = text("""
    SELECT * FROM Schedule AS S
    WHERE
        S.fMeasurementTypeKey IN {keys}
    AND
        S.fStart < "{now}"
    ORDER BY S.fStart DESC
    LIMIT 1
    """.format(
        keys=(
            types.loc["Startup"].fMeasurementTypeKey,
            types.loc["Shutdown"].fMeasurementTypeKey
        ),
        now=current_time_rounded_to_seconds
    ))

    with db.connect() as conn:
        return pd.merge(
            pd.read_sql_query(query, conn),
            types.reset_index(),
            on="fMeasurementTypeKey"
        )


@log_call_and_result
@retry(stop_max_delay=30000,  # 30 seconds max
       wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
       wait_exponential_max=1000,  # but wait 1 second per try maximum
       )
def is_shift_at_the_moment(time=None, db=None):
    '''There is a shift at the moment'''
    if time is None:
        now = now_seconds()
    else:
        now = time.replace(microsecond=0)

    last_entry = get_last_startup_or_shutdown(
        current_time_rounded_to_seconds=now,
        db=db
    )
    name = last_entry.iloc[0].fMeasurementTypeName
    return name == "Startup"


def get_next_shutdown(current_time_rounded_to_seconds=None, db=None):
    if current_time_rounded_to_seconds is None:
        current_time_rounded_to_seconds = now_seconds()

    if db is None:
        db = tools.create_db_connection()

    types = get_MeasurementType(db)
    query = text("""
    SELECT * FROM Schedule AS S
    WHERE
        S.fMeasurementTypeKey = {key}
    AND
        S.fStart > "{now}"
    ORDER BY S.fStart ASC
    LIMIT 1
    """.format(
        key=(types.loc["Shutdown"].fMeasurementTypeKey),
        now=current_time_rounded_to_seconds
    ))

    try:
        with db.connect() as conn:
            return pd.merge(
                pd.read_sql_query(query, conn),
                types.reset_index(),
                on="fMeasurementTypeKey"
            ).iloc[0].fStart.tz_localize(UTC)
    except IndexError:
        # in case we cannot find the next shutdown,
        # we simply say the next shutdown is waaaay far in the future.
        return datetime.max.replace(tzinfo=timezone.utc)


def get_last_shutdown(current_time_rounded_to_seconds=None, db=None):
    try:
        if current_time_rounded_to_seconds is None:
            current_time_rounded_to_seconds = now_seconds()
        if db is None:
            db = tools.create_db_connection()

        types = get_MeasurementType(db)
        query = text("""
        SELECT * FROM Schedule AS S
        WHERE
            S.fMeasurementTypeKey = {key}
        AND
            S.fStart < "{now}"
        ORDER BY S.fStart DESC
        LIMIT 1
        """.format(
            key=(types.loc["Shutdown"].fMeasurementTypeKey),
            now=current_time_rounded_to_seconds
        ))

        with db.connect() as conn:
            return pd.merge(
                pd.read_sql_query(query, conn),
                types.reset_index(),
                on="fMeasurementTypeKey"
            ).iloc[0].fStart.tz_localize(UTC)
    except IndexError:
        # in case we cannot find the last shutdown,
        # we simply say the last shutdown was waaay in the past
        return datetime.min.replace(tzinfo=timezone.utc)
