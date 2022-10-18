from custos.notify import levels
import json
from datetime import datetime, timezone, timedelta


UTC = timezone.utc


def read_alerts(path, timestamp=None):
    with open(path) as f:
        alerts = json.load(f)

    for alert in alerts:
        if timestamp is not None:
            alert['timestamp'] = timestamp
        else:
            alert['timestamp'] = datetime.fromisoformat(alert['timestamp']).replace(tzinfo=UTC)

    return alerts

def test_message_level_all_acknowledged():
    from shifthelper.checks import message_level

    alerts = read_alerts(
        'tests/resources/all_acknowledged.json',
        timestamp=datetime.now(UTC),
    )

    assert message_level(checkname='WindGustCheck', alerts=alerts) == levels.INFO


def test_message_level_all_acknowledged_but_old():
    from shifthelper.checks import message_level

    alerts = read_alerts('tests/resources/all_acknowledged.json')
    print(alerts)
    assert message_level(checkname='WindGustCheck', alerts=alerts) == levels.WARNING


def test_all_acknowledged():
    from shifthelper.checks import all_recent_alerts_acknowledged

    alerts = read_alerts('tests/resources/all_acknowledged.json')
    print(alerts)
    assert not all_recent_alerts_acknowledged(
        checkname='WindGustCheck', alerts=alerts, result_if_no_alerts=False
    )
    assert all_recent_alerts_acknowledged(
        checkname='WindGustCheck', alerts=alerts, result_if_no_alerts=True
    )


def test_message_level_all_acknowledged_1():
    from shifthelper.checks import message_level

    timestamp = datetime.now(timezone.utc)
    alerts = read_alerts('tests/resources/not_all_acknowledged.json', timestamp)
    print(alerts)
    for i, alert in enumerate(alerts, start=1):
        alert['timestamp'] -= timedelta(minutes=i)

    assert message_level(checkname='WindGustCheck', alerts=alerts) == levels.WARNING
    assert message_level(checkname='MainJSStatusCheck', alerts=alerts) == levels.WARNING


def test_message_level_not_all_acknowledged_2():
    from shifthelper.checks import message_level

    timestamp = datetime.now(UTC)
    alerts = read_alerts('tests/resources/not_all_acknowledged.json', timestamp)

    assert message_level(checkname='WindGustCheck', alerts=alerts) == levels.WARNING
    assert message_level(checkname='MainJsStatusCheck', alerts=alerts) == levels.INFO


def test_empty():
    from shifthelper.checks import all_recent_alerts_acknowledged

    alerts = read_alerts('tests/resources/no_alerts.json')

    assert all_recent_alerts_acknowledged(alerts=alerts, result_if_no_alerts=True)
    assert not all_recent_alerts_acknowledged(alerts=alerts, result_if_no_alerts=False)
