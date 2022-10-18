from freezegun import freeze_time
from sqlalchemy import create_engine


def test_get_current_shifter():
    from shifthelper.tools.shift import get_current_shifter

    db = create_engine('sqlite:///tests/resources/database/cloned_db.sqlite')

    with freeze_time('2016-12-20 21:00:00'):
        shifter = get_current_shifter(db=db)

        assert shifter['username'] == 'kbruegge'
