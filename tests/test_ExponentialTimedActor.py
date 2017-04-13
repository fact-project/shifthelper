from freezegun import freeze_time
from datetime import datetime, timedelta
import numpy as np

test_value = 0


def set_test_value(n):
    global test_value
    test_value = n
    print(test_value, datetime.utcnow())


def test_ExponentialTimedActor():
    from shifthelper.checks import ExponentialTimedActor

    timed_set_test_value = ExponentialTimedActor(
        action=set_test_value,
        maximum_pause=timedelta(minutes=10),
    )

    initial_datetime = datetime(2016, 1, 1)
    with freeze_time(initial_datetime) as frozen_datetime:

        # test time: 3600 seconds = 1 hour
        for i in range(3600):
            frozen_datetime.move_to(initial_datetime + timedelta(seconds=i))
            timed_set_test_value(test_value + 1)

        # test time 1 hour:
        # 1: immediately @ 2016-01-01 00:00:00
        # 2: after 1min  @ 2016-01-01 00:01:00
        # 3: after 2min  @ 2016-01-01 00:03:00
        # 4: after 4min  @ 2016-01-01 00:07:00
        # 5: after 8min  @ 2016-01-01 00:15:00
        # 6: after 10min @ 2016-01-01 00:25:00, c.f. maximum_pause
        # 7: after 10min @ 2016-01-01 00:35:00
        # 8: after 10min @ 2016-01-01 00:45:00
        # 9: after 10min @ 2016-01-01 00:55:00
        assert test_value == 9

    global test_value
    test_value = 0

def test_ExponentialTimedActor_with_reset():
    from shifthelper.checks import ExponentialTimedActor

    timed_set_test_value = ExponentialTimedActor(
        action=set_test_value,
        maximum_pause=timedelta(minutes=10),
    )

    initial_datetime = datetime(2016, 1, 1)
    with freeze_time(initial_datetime) as frozen_datetime:

        # test time: 3600 seconds = 1 hour
        for i in range(1800):
            frozen_datetime.move_to(initial_datetime + timedelta(seconds=i))
            timed_set_test_value(test_value + 1)

        timed_set_test_value.reset()  # after 30 minutes

        for i in range(1800, 3600):
            frozen_datetime.move_to(initial_datetime + timedelta(seconds=i))
            timed_set_test_value(test_value + 1)

        # 1:  00:00h  immediate
        # 2:  00:01h  + 1min
        # 3:  00:03h  + 2min
        # 4:  00:07h  + 4min
        # 5:  00:15h  + 8min
        # 6:  00:25h  + 10min
        # 7:  00:30h  immediate after reset
        # 8:  00:31h  + 1min
        # 9:  00:33h  + 2min
        # 10: 00:37h  + 4min
        # 11: 00:45h  + 8min
        # 12: 00:55h  + 10min
        assert test_value == 12

    global test_value
    test_value = 0
