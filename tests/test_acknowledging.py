import pandas as pd
from datetime import datetime


def test_all_ackownledged():
    from shifthelper.checks import all_recent_alerts_acknowledged

    alerts = pd.read_json('tests/resources/all_acknowledged.json')
    # shift time of the alerts so that they happend recently
    alerts.timestamp = pd.date_range(datetime.utcnow(), periods=len(alerts), freq='m')

    assert all_recent_alerts_acknowledged(alerts=alerts)
    assert all_recent_alerts_acknowledged(checkname='WindGustCheck', alerts=alerts)


def test_not_all_ackownledged():
    from shifthelper.checks import all_recent_alerts_acknowledged

    alerts = pd.read_json('tests/resources/not_all_acknowledged.json')
    # shift time of the alerts so that they happend recently
    alerts.timestamp = pd.date_range(datetime.utcnow(), periods=len(alerts), freq='m')

    assert not all_recent_alerts_acknowledged(alerts=alerts)
    assert not all_recent_alerts_acknowledged(checkname='WindGustCheck', alerts=alerts)
    assert all_recent_alerts_acknowledged(checkname='MainJSStatusCheck', alerts=alerts)


def test_empty():
    from shifthelper.checks import all_recent_alerts_acknowledged

    alerts = pd.read_json('tests/resources/no_alerts.json')

    assert all_recent_alerts_acknowledged(alerts=alerts)
    assert all_recent_alerts_acknowledged(checkname='WindGustCheck', alerts=alerts)
    assert all_recent_alerts_acknowledged(
        checkname='MainJSStatusCheck', check_time=None, alerts=alerts
    )


def test_no_windgust():
    from shifthelper.checks import all_recent_alerts_acknowledged

    alerts = pd.read_json('tests/resources/no_WindGustCheck.json')

    assert all_recent_alerts_acknowledged(checkname='WindGustCheck', alerts=alerts)


def test_level():
    from shifthelper.checks import message_level
    from custos.notify import levels
    alerts = pd.read_json('tests/resources/not_all_acknowledged.json')
    # shift time of the alerts so that they happend recently
    alerts.timestamp = pd.date_range(datetime.utcnow(), periods=len(alerts), freq='m')

    assert message_level(checkname='WindGustCheck', alerts=alerts) == levels.WARNING
    assert message_level(checkname='MainJSStatusCheck', alerts=alerts) == levels.INFO
