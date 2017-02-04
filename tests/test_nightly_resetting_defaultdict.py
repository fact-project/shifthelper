from freezegun import freeze_time
import datetime
import numpy as np

def test_NightlyResettingDefaultdict():
    from shifthelper.tools import NightlyResettingDefaultdict

    initial_datetime = datetime.datetime(2016, 1, 1)
    two_days_later = datetime.datetime(2016, 1, 3, 0, 0, 0)

    with freeze_time(initial_datetime) as frozen_datetime:
        nightly_max_rate = NightlyResettingDefaultdict(lambda: -np.inf)
        nightly_max_rate['foo'] = 5

        assert nightly_max_rate['foo'] == 5
        frozen_datetime.move_to(two_days_later)

        assert nightly_max_rate['foo'] == -np.inf
        nightly_max_rate['foo'] = 6
        assert nightly_max_rate['foo'] == 6
