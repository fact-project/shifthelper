import pandas as pd
from datetime import datetime


def test_all_ackownledged():
    from shifthelper.checks import all_recent_alerts_acknowledged

    alerts = pd.read_json('tests/resources/all_acknowledged.json')
    # shift time of the alerts so that they happend recently
    alerts.timestamp = pd.date_range(datetime.utcnow(), periods=len(alerts), freq='m')

    assert all_recent_alerts_acknowledged(alerts)
    assert all_recent_alerts_acknowledged(alerts, checkname='WindGustCheck')


def test_not_all_ackownledged():
    from shifthelper.checks import all_recent_alerts_acknowledged

    alerts = pd.read_json('tests/resources/not_all_acknowledged.json')
    # shift time of the alerts so that they happend recently
    alerts.timestamp = pd.date_range(datetime.utcnow(), periods=len(alerts), freq='m')

    assert not all_recent_alerts_acknowledged(alerts)
    assert not all_recent_alerts_acknowledged(alerts, checkname='WindGustCheck')
    assert all_recent_alerts_acknowledged(alerts, checkname='MainJSStatusCheck')


def test_empty():
    from shifthelper.checks import all_recent_alerts_acknowledged

    alerts = pd.read_json('tests/resources/no_alerts.json')

    assert all_recent_alerts_acknowledged(alerts)
    assert all_recent_alerts_acknowledged(alerts, checkname='WindGustCheck')
    assert all_recent_alerts_acknowledged(
        alerts, checkname='MainJSStatusCheck', check_time=None
    )


def test_no_windgust():
    from shifthelper.checks import all_recent_alerts_acknowledged

    alerts = pd.read_json('tests/resources/no_WindGustCheck.json')

    assert all_recent_alerts_acknowledged(alerts, checkname='WindGustCheck')
