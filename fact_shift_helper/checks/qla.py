# -*- coding:utf-8 -*-
from __future__ import print_function, division, absolute_import
import os
import numpy as np
import pandas as pd

from collections import defaultdict
import sqlalchemy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from . import Check
from .. import tools
from ..unused.handle_statistics import *

if not os.path.exists('plots'):
    os.makedirs('plots')


def create_alert_rate():
    config = tools.read_config_file('config.ini')
    alert_rate = defaultdict(lambda: config.getint('qla', 'default'))
    for key, val in config.items('qla'):
        if key not in ['default', ]:
            alert_rate[key] = int(val)
    return alert_rate

colors = ['red', 'blue', 'green', 'black', 'cyan', 'yellow']

def create_db_connection():
    config = tools.read_config_file('config.ini')    
    factdb = sqlalchemy.create_engine(
        "mysql+pymysql://{user}:{pw}@{host}/{db}".format(
            user=config.get('database', 'user'),
            pw=config.get('database', 'password'),
            host=config.get('database', 'host'),
            db=config.get('database', 'database'),
        )
    )
    return factdb


class FlareAlert(Check):
    max_rate = defaultdict(lambda: 0)

    def check(self):
        data = get_data()
        if data is None:
            return
        if len(data.index) == 0:
            return

        create_mpl_plot(data)

        # cut in significance > 3.0
        data = data[data.significance > 3.]

        qla_max_rates = data.groupby('fSourceName').agg({
            'rate': 'max',
            'fSourceKEY': 'median',
        })


        for source, data in qla_max_rates.iterrows():
            rate = float(data['rate'])
            self.update_qla_data(source, '{:3.1f}'.format(rate))
            if rate > self.max_rate[source]:
                self.max_rate[source] = rate
                if self.max_rate[source] > create_alert_rate()[source]:
                    msg = 'Source {} over alert rate: {:3.1f} Events/h'
                    self.queue.append(msg.format(source, self.max_rate[source]))


def get_data(bin_width_minutes=20, timestamp=None):
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
        night=tools.night_integer(timestamp),
    )

    data = pd.read_sql_query(
        sql_query,
        create_db_connection(),
        parse_dates=['fRunStart', 'fRunStop'],
    )
    # drop rows with NaNs from the table, these are unfinished qla results
    data.dropna(inplace=True)

    # if no qla data is available, return None
    if len(data.index) == 0:
        return None

    data.sort('fRunStart', inplace=True)
    data.index = np.arange(len(data.index))

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
        valid = agg.fOnTimeAfterCuts >= 0.9 * 60 * bin_width_minutes
        binned = binned.append(agg[valid], ignore_index=True)

    binned['significance'] = np.zeros_like(binned.rate)
    
    for i in range(len(binned)):
        binned.loc[i, 'significance'] = S_Li_Ma(binned.iloc[i].fNumSigEvts, binned.iloc[i].fNumBgEvts*5)

    return binned


def create_mpl_plot(data):
    plt.figure()
    for name, group in data.groupby('fSourceName'):
        if len(group.index) == 0:
            continue
        plt.errorbar(
            x=group.timeMean.values,
            y=group.rate.values,
            xerr=group.xerr.values,
            yerr=group.yerr.values,
            label=name,
            fmt='o',
            mec='none',
        )
    plt.legend(loc='best')
    plt.tight_layout()
    plt.savefig('plots/qla.png')
    plt.close('all')


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
    '''
    draw an errorbar plot with bokeh
    '''

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
