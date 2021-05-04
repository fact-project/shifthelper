from .. import tools
from datetime import datetime, timezone
from retrying import retry
from sqlalchemy import text

from ..debug_log_wrapper import log_call_and_result


UTC = timezone.utc


last_startup_or_shutdown_query = query = text("""
SELECT * FROM `Schedule`
JOIN `MeasurementType` ON `Schedule`.`fMeasurementTypeKey` = `MeasurementType`.`fMeasurementTypeKey`
WHERE
    `fMeasurementTypeName` in ("Startup", "Shutdown")
    AND `fStart` < :now
ORDER BY `fStart` DESC
LIMIT 1
""")


next_shutdown_query = query = text("""
SELECT * FROM `Schedule`
JOIN `MeasurementType` ON `Schedule`.`fMeasurementTypeKey` = `MeasurementType`.`fMeasurementTypeKey`
WHERE
    `fMeasurementTypeName` = "Shutdown"
    AND `fStart` > :now
ORDER BY `fStart` ASC
LIMIT 1
""")

last_shutdown_query = query = text("""
SELECT * FROM `Schedule`
JOIN `MeasurementType` ON `Schedule`.`fMeasurementTypeKey` = `MeasurementType`.`fMeasurementTypeKey`
WHERE
    `fMeasurementTypeName` = "Shutdown"
    AND `fStart` < :now
ORDER BY `fStart` DESC
LIMIT 1
""")



def now_seconds(tz=UTC):
    '''Current time rounded to full seconds, by default with tz UTC'''
    return datetime.now(tz=tz).replace(microsecond=0)


def get_last_startup_or_shutdown(
    current_time_rounded_to_seconds=None,
    db=None
):
    if current_time_rounded_to_seconds is None:
        current_time_rounded_to_seconds = now_seconds()

    if db is None:
        db = tools.create_db_connection()

    parameters = dict(now=current_time_rounded_to_seconds)
    with db.begin() as con:
        result = con.execute(last_startup_or_shutdown_query, parameters).first()

    if result is not None:
        return result._mapping


@log_call_and_result
@retry(
    stop_max_delay=30000,  # 30 seconds max
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
    if last_entry is None:
        return False

    return last_entry['fMeasurementTypeName'] == "Startup"


def get_next_shutdown(current_time_rounded_to_seconds=None, db=None):
    if current_time_rounded_to_seconds is None:
        current_time_rounded_to_seconds = now_seconds()

    if db is None:
        db = tools.create_db_connection()

    with db.begin() as con:
        parameters = dict(now=current_time_rounded_to_seconds)
        next_shutdown = con.execute(next_shutdown_query, parameters).first()

    if next_shutdown is None:
        # in case we cannot find the next shutdown,
        # we simply say the next shutdown is waaaay far in the future.
        return datetime.max.replace(tzinfo=timezone.utc)

    return next_shutdown._mapping['fStart'].replace(tzinfo=timezone.utc)


def get_last_shutdown(current_time_rounded_to_seconds=None, db=None):
    if current_time_rounded_to_seconds is None:
        current_time_rounded_to_seconds = now_seconds()

    if db is None:
        db = tools.create_db_connection()

    with db.begin() as con:
        parameters = dict(now=current_time_rounded_to_seconds)
        last_shutdown = con.execute(last_shutdown_query, parameters).first()

    if last_shutdown is None:
        # in case we cannot find the last shutdown,
        # we simply say the last shutdown was waaay in the past
        return datetime.min.replace(tzinfo=timezone.utc)

    return last_shutdown._mapping['fStart'].replace(tzinfo=timezone.utc)
