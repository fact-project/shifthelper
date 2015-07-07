from collections import defaultdict
from blessings import Terminal
term = Terminal()
from sqlalchemy import create_engine
import pandas as pd
from bokeh.plotting import figure, output_file, save

import fact
from fact_exceptions import QLAException

max_rate = defaultdict(lambda: 0)
alert_rate = defaultdict(lambda: 10)
alert_rate['Mrk 501'] = 45
alert_rate['Mrk 421'] = 45

colors = ['red', 'blue', 'green', 'black', 'cyan', 'yellow']


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
    """
    sql_query = sql_query.format(
        comma_sep_keys=', '.join(keys),
        night=fact.night_integer(),
    )

    data = pd.read_sql_query(sql_query, factdb, parse_dates=['fRunStart'])
    # drop rows with NaNs from the table, these are unfinished qla results
    data = data.dropna()

    # if no qla data is available, return None
    if len(data.index) == 0:
        return None
    data.set_index('fRunStart', inplace=True)
    # group by source to do the analysis seperated for each one
    grouped = data.groupby('fSourceName')
    # resample in 20 min intervals by summing up events and ontime
    binned = grouped.resample(
        '20Min',
        how={'fNumExcEvts': 'sum', 'fOnTimeAfterCuts': 'sum'},
    )
    # throw away bins with less than 5 minutes of datataking
    binned = binned.query('fOnTimeAfterCuts >= 300')
    if len(binned.index) == 0:
        return None

    # calculate excess events per hour
    binned['rate'] = binned.fNumExcEvts / binned.fOnTimeAfterCuts * 3600

    create_bokeh_plot(binned)

    # get the maximum rate for each source
    max_rate = binned.groupby(level='fSourceName').aggregate({'rate': 'max'})
    return max_rate


def create_bokeh_plot(data):
    '''create bokeh plot at www.fact-project.org/qla
    expects a pandas dataframe with 2 level index, Source, Time
    '''
    output_file('qla.html', title='ShiftHelper QLA')
    fig = figure(width=600, height=400, x_axis_type='datetime')
    for i, source in enumerate(data.index.levels[0]):
        fig.circle(
            x=data.loc[source].index.values,
            y=data.loc[source].rate,
            legend=source,
            color=colors[i],
        )
    legend = fig.legend[0]
    legend.orientation = 'top_left'
    save(fig)


def perform_checks():
    """ raise ValueError if new flare detected.

    If the maximum excess rates are over the alter_rates for a source
    and also higher than before, throw a ValueErrorm which leads to
    a skype-call inside the main while loop of shift_helper.py
    """
    qla_max_rates = get_max_rates()
    if qla_max_rates is None:
        print('No QLA data available yet')
        return

    print('max rates of today:')
    for source, rate in qla_max_rates.iterrows():
        rate = float(rate)
        if rate > max_rate[source]:
            max_rate[source] = rate
            if max_rate[source] > alert_rate[source]:
                msg = term.red(
                    '    !!!! Source {} over alert rate: {:3.1f} Events/h')
                raise QLAException(msg.format(source, max_rate[source]))
        print('{} : {:3.1f} Events/h'.format(source, max_rate[source]))
