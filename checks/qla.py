# -*- coding:utf-8 -*-
from __future__ import print_function, division, absolute_import
import os
import numpy as np
import pandas as pd

from collections import defaultdict
from sqlalchemy import create_engine
from bokeh.plotting import figure, output_file, save

from ConfigParser import SafeConfigParser
import fact
from . import Check

if not os.path.exists('plots'):
    os.makedirs('plots')

config = SafeConfigParser()
config.optionxform = str  # this make the parsing case sensitive
config.read('config.ini')

alert_rate = defaultdict(lambda: config.getint('qla', 'default'))
for key, val in config.items('qla'):
    if key not in ['default', ]:
        alert_rate[key] = int(val)

colors = ['red', 'blue', 'green', 'black', 'cyan', 'yellow']

factdb = create_engine(
    "mysql+mysqldb://{user}:{pw}@{host}/{db}".format(
        user=config.get('database', 'user'),
        pw=config.get('database', 'password'),
        host=config.get('database', 'host'),
        db=config.get('database', 'database'),
    )
)

class FlareAlert(Check):
    max_rate = defaultdict(lambda: 0)

    def check(self):
        data = get_data()
        if data is None:
            return
        qla_max_rates = data.groupby('fSourceName').agg({
            'rate': 'max',
            'fSourceKEY': 'median',
        })

        create_bokeh_plot(data)

        for source, data in qla_max_rates.iterrows():
            rate = float(data['rate'])
            if rate > self.max_rate[source]:
                self.max_rate[source] = rate
                if self.max_rate[source] > alert_rate[source]:
                    msg = 'Source {} over alert rate: {:3.1f} Events/h'
                    self.queue.append(msg.format(source, self.max_rate[source]))


def get_data(bin_width_minutes=20):
    ''' this will get the QLA results to call if you have to send an alert '''
    keys = [
        'QLA.fRunID',
        'QLA.fNight',
        'QLA.fNumExcEvts',
        'QLA.fNumSigEvts',
        'QLA.fNumBgEvts',
        'QLA.fOnTimeAfterCuts',
        'RunInfo.fRunStart',
        'RunInfo.fRunStop',
        'Source.fSourceName',
        'Source.fSourceKEY',
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

    data = pd.read_sql_query(
        sql_query,
        factdb,
        parse_dates=['fRunStart', 'fRunStop'],
    )
    # drop rows with NaNs from the table, these are unfinished qla results
    data.dropna(inplace=True)
    data.sort('fRunStart', inplace=True)
    data.index = np.arange(len(data.index))

    # if no qla data is available, return None
    if len(data.index) == 0:
        return None

    # group by source to do the analysis seperated for each one
    grouped = data.groupby('fSourceName')
    binned = pd.DataFrame()
    for source, group in grouped:
        group = group.copy()
        group['bin'] = dorner_binning(group, bin_width_minutes)
        agg = group.groupby('bin').aggregate({
            'fOnTimeAfterCuts': 'sum',
            'fNumExcEvts':      'sum',
            'fNumSigEvts':      'sum',
            'fNumBgEvts':       'sum',
            'fRunStart':        'min',
            'fRunStop':         'max',
            'fSourceKEY':       'median',
        })
        agg['fSourceName'] = source
        agg['rate'] = agg.fNumExcEvts / agg.fOnTimeAfterCuts * 3600
        agg['xerr'] = (agg.fRunStop - agg.fRunStart) / 2
        agg['timeMean'] = agg.fRunStart + agg.xerr
        agg['yerr'] = np.sqrt(np.abs(agg.fNumSigEvts) + np.abs(agg.fNumExcEvts))
        agg['yerr'] /= agg.fOnTimeAfterCuts / 3600
        valid = agg.query('fOnTimeAfterCuts > 0.9*60*{}'.format(bin_width_minutes))
        binned = binned.append(valid, ignore_index=True)
    return binned


def create_bokeh_plot(data):
    '''create bokeh plot at www.fact-project.org/qla
    '''
    output_file('plots/qla.html', title='ShiftHelper QLA')
    fig = figure(width=600, height=400, x_axis_type='datetime')
    for i, (name, group) in enumerate(data.groupby('fSourceName')):
        errorbar(
            fig=fig,
            x=group.timeMean.values,
            y=group.rate.values,
            xerr=group.xerr.values,
            yerr=group.yerr.values,
            legend=name,
            color=colors[i],
        )
    legend = fig.legend[0]
    legend.orientation = 'top_left'
    save(fig)


def errorbar(
        fig,
        x,
        y,
        xerr=None,
        yerr=None,
        color='red',
        legend=None,
        point_kwargs={},
        error_kwargs={},
        ):

    fig.circle(x, y, color=color, legend=legend, **point_kwargs)


    if xerr is not None:
        x_err_x = []
        x_err_y = []
        for px, py, err in zip(x, y, xerr):
            x_err_x.append((px - err, px + err))
            x_err_y.append((py, py))
        fig.multi_line(x_err_x, x_err_y, color=color, **error_kwargs)

    if yerr is not None:
        y_err_x = []
        y_err_y = []
        for px, py, err in zip(x, y, yerr):
            y_err_x.append((px, px))
            y_err_y.append((py - err, py + err))
        fig.multi_line(y_err_x, y_err_y, color=color, **error_kwargs)


def dorner_binning(data, bin_width_minutes=20):
    bin_number = 0
    ontime_sum = 0
    bins = []
    for key, row in data.iterrows():
        if ontime_sum + row.fOnTimeAfterCuts >= bin_width_minutes * 60:
            bin_number += 1
            ontime_sum = 0
        bins.append(bin_number)
        ontime_sum += row['fOnTimeAfterCuts']
    return pd.Series(bins, index=data.index)
