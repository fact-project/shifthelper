import pandas as pd
from datetime import datetime
from custos.notify import levels


def test_message_level_all_acknowledged():
    from shifthelper.checks import message_level

    alerts = pd.read_json('tests/resources/all_acknowledged.json')
    # shift time of the alerts so that they happend recently
    alerts['timestamp'] = datetime.utcnow()

    assert message_level(checkname='WindGustCheck', alerts=alerts) == levels.INFO


def test_message_level_all_acknowledged_but_old():
    from shifthelper.checks import message_level
    alerts = pd.read_json('tests/resources/all_acknowledged.json')

    assert message_level(checkname='WindGustCheck', alerts=alerts) == levels.WARNING


def test_all_acknowledged():
    from shifthelper.checks import all_recent_alerts_acknowledged
    alerts = pd.read_json('tests/resources/all_acknowledged.json')

    assert not all_recent_alerts_acknowledged(
        checkname='WindGustCheck', alerts=alerts, result_if_no_alerts=False
    )
    assert all_recent_alerts_acknowledged(
        checkname='WindGustCheck', alerts=alerts, result_if_no_alerts=True
    )


def test_message_level_all_acknowledged_1():
    from shifthelper.checks import message_level

    alerts = pd.read_json('tests/resources/not_all_acknowledged.json')
    # shift time of the alerts so that they happend recently
    alerts.timestamp = pd.date_range(datetime.utcnow(), periods=len(alerts), freq='-1min')
    print(alerts)

    assert message_level(checkname='WindGustCheck', alerts=alerts) == levels.WARNING
    assert message_level(checkname='MainJSStatusCheck', alerts=alerts) == levels.WARNING


def test_message_level_not_all_acknowledged_2():
    from shifthelper.checks import message_level

    alerts = pd.read_json('tests/resources/not_all_acknowledged.json')
    # shift time of the alerts so that they happend recently
    alerts['timestamp'] = datetime.utcnow()
    print(alerts)

    assert message_level(checkname='WindGustCheck', alerts=alerts) == levels.WARNING
    assert message_level(checkname='MainJsStatusCheck', alerts=alerts) == levels.INFO


def test_empty():
    from shifthelper.checks import all_recent_alerts_acknowledged

    alerts = pd.read_json('tests/resources/no_alerts.json')

    assert all_recent_alerts_acknowledged(alerts=alerts, result_if_no_alerts=True)
    assert not all_recent_alerts_acknowledged(alerts=alerts, result_if_no_alerts=False)
