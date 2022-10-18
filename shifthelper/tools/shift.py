import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import text

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


shifter_query = text('''
SELECT
    u AS username,
    fid5 AS phone_mobile,
    fid9 AS telegram_id,
    email
FROM calendar_data
LEFT JOIN users ON calendar_data.u = users.username
LEFT JOIN userfields ON users.uid = userfields.ufid
WHERE y=:y AND m=:m and d=:d AND NOT x
''')


def get_current_shifter(db=None):
    night = (datetime.now(timezone.utc) - timedelta(hours=12)).date()

    if db is None:
        db = tools.create_db_connection()

    with db.begin() as con:
        # Date.GetMonth starts at 0 in javascript
        parameters = dict(y=night.year, m=night.month - 1, d=night.day)
        shifters = con.execute(shifter_query, parameters).all()

    if len(shifters) > 1:
        log.warning('Found more than two shifters, choosing first')

    shifter = shifters[0]._mapping
    log.debug(f'Found shifter: {shifter["username"]}')
    return shifter
