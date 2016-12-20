from freezegun import freeze_time
from sqlalchemy import create_engine


def test_is_shift():
    from shifthelper.tools.is_shift import is_shift_at_the_moment

    db = create_engine('sqlite:///tests/resources/database/cloned_db.sqlite')

    with freeze_time('2016-12-18 16:00:00'):
        assert not is_shift_at_the_moment(db=db)

    with freeze_time('2016-12-18 23:00:00'):
        assert is_shift_at_the_moment(db=db)
