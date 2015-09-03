from datetime import datetime
from datetime import timedelta

def night(timestamp=None):
    """
    gives the date for a day change at noon instead of midnight
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    if timestamp.hour < 12:
        timestamp = timestamp - timedelta(days=1)
    return timestamp


def night_integer(timestamp=None):
    """ get the correct night in fact format
        if it is after 0:00, take the date
        of yesterday
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    if timestamp.hour < 12:
        timestamp = timestamp - timedelta(days=1)
    night = int(timestamp.strftime('%Y%m%d'))
    return night