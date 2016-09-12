import pandas as pd
from .. import tools
from functools import lru_cache
from datetime import datetime
from datetime import timedelta


@lru_cache(1)
def get_MeasurementType(db=None):
    if db is None:
        db = tools.create_db_connection()
    df = pd.read_sql_query("select * from factdata.MeasurementType", db)
    df.set_index("fMeasurementTypeName", inplace=True)
    return df

@lru_cache(10)
def get_last_startup_or_shutdown(current_time_rounded_to_seconds, db=None):
    if db is None:
        db = tools.create_db_connection()

    types = get_MeasurementType(db)
    query = """
    SELECT * FROM factdata.Schedule AS S 
    WHERE 
        S.fMeasurementTypeKey IN {keys}
    AND
        S.fStart < "{now}"
    GROUP BY S.fStart ASC
    LIMIT 1
    """.format(
        keys=(types.loc["Startup"].fMeasurementTypeKey,
            types.loc["Shutdown"].fMeasurementTypeKey),
        now=current_time_rounded_to_seconds
        )
    
    return pd.merge(
        pd.read_sql_query(query, db),
        types.reset_index(), 
        on="fMeasurementTypeKey"
    )


def is_shift_at_the_moment(time):
    now = datetime.utcnow().replace(microsecond=0)
    last_entry = get_last_startup_or_shutdown(current_time_rounded_to_seconds=now, db=None)
    name = last_entry.iloc[0].fMeasurementTypeName
    return name == "Startup"
