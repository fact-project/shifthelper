import pandas as pd
from .. import tools
from functools import lru_cache
from datetime import datetime
from retrying import retry


@lru_cache(1)
def get_MeasurementType(db=None):
    if db is None:
        db = tools.create_db_connection(tools.config['cloned_db'])
    df = pd.read_sql_query("select * from factdata_MeasurementType", db)
    df.set_index("fMeasurementTypeName", inplace=True)
    return df


def get_last_startup_or_shutdown(current_time_rounded_to_seconds=None, db=None):
    if current_time_rounded_to_seconds is None:
        current_time_rounded_to_seconds = datetime.utcnow().replace(microsecond=0)
    if db is None:
        db = tools.create_db_connection(tools.config['cloned_db'])

    types = get_MeasurementType(db)
    query = """
    SELECT * FROM factdata_Schedule AS S
    WHERE
        S.fMeasurementTypeKey IN {keys}
    AND
        S.fStart < "{now}"
    ORDER BY S.fStart DESC
    LIMIT 1
    """.format(
        keys=(
            types.loc["Startup"].fMeasurementTypeKey,
            types.loc["Shutdown"].fMeasurementTypeKey),
        now=current_time_rounded_to_seconds
        )

    return pd.merge(
        pd.read_sql_query(query, db),
        types.reset_index(),
        on="fMeasurementTypeKey"
    )


@retry(stop_max_delay=30000,  # 30 seconds max
       wait_exponential_multiplier=100,  # wait 2^i * 100 ms, on the i-th retry
       wait_exponential_max=1000,  # but wait 1 second per try maximum
       )
def is_shift_at_the_moment(time=None):
    if time is None:
        now = datetime.utcnow().replace(microsecond=0)
    else:
        now = time.replace(microsecond=0)
    last_entry = get_last_startup_or_shutdown(current_time_rounded_to_seconds=now, db=None)
    name = last_entry.iloc[0].fMeasurementTypeName
    return name == "Startup"
