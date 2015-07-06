from collections import defaultdict
from blessings import Terminal
term = Terminal()
from sqlalchemy import create_engine
import pandas as pd
import fact

max_rate = defaultdict(lambda: 0)
alert_rate = defaultdict(lambda: 10)
alert_rate['Mrk 501'] = 45
alert_rate['Mrk 421'] = 45

factdb = None


def setup():
    global factdb
    factdb = create_engine(
        "mysql+mysqldb://<databasecredentials>")


def get_max_rates():
    ''' this will get the QLA results to call if you have to send an alert '''
    keys = [
        'QLA.fRunID',
        'QLA.fNight',
        'QLA.fNumExcEvts',
        'QLA.fOnTimeAfterCuts',
        'RunInfo.fRunStart',
        'Source.fSourceName',
    ]

    sql_query = """SELECT {comma_sep_keys}
        FROM AnalysisResultsRunLP QLA
        LEFT JOIN RunInfo
        ON QLA.fRunID = RunInfo.fRunID AND QLA.fNight = RunInfo.fNight
        LEFT JOIN Source
        ON RunInfo.fSourceKEY = Source.fSourceKEY
        WHERE QLA.fNight = {night:d}
        """.format(
        comma_sep_keys=', '.join(keys),
        night=fact.night_int())

    data = pd.read_sql_query(sql_query, factdb, parse_dates=['fRunStart'])
    # if no qla data is available, return None
    data = data.dropna()
    if len(data.index) == 0:
        return None
    data.set_index('fRunStart', inplace=True)
    grouped = data.groupby('fSourceName')
    binned = grouped.resample(
        '20Min',
        how={'fNumExcEvts': 'sum', 'fOnTimeAfterCuts': 'sum'},
    )
    binned['rate'] = binned.fNumExcEvts / binned.fOnTimeAfterCuts * 3600
    max_rate = binned.groupby(level='fSourceName').aggregate({'rate': 'max'})
    return max_rate


def perform_checks():
    qla_max_rates = get_max_rates()
    if qla_max_rates is None:
        print('No QLA data available yet')
    else:
        print('max rates of today:')
        for source, rate in qla_max_rates.iterrows():
            rate = float(rate)
            if rate > max_rate[source]:
                max_rate[source] = rate
                if max_rate[source] > alert_rate[source]:
                    msg = term.red(
                        '    !!!! Source {} over alert rate: {:3.1f} Events/h')
                    raise ValueError(msg.format(source, max_rate[source]))
            print('{} : {:3.1f} Events/h'.format(source, max_rate[source]))
