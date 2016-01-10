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

colors = ['red', 'blue', 'green', 'black', 'cyan', 'yellow']

outdir = os.path.join(os.environ['HOME'], '.shifthelper', 'plots')
if not os.path.exists(outdir):
    os.makedirs(outdir)


def create_alert_rate():
    config = tools.read_config_file()
    alert_rate = defaultdict(lambda: config.getint('qla', 'default'))
    for key, val in config.items('qla'):
        if key not in ['default', ]:
            alert_rate[key] = int(val)
    return alert_rate


def create_db_connection():
    config = tools.read_config_file()
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

        significant = data.query('significance >= 3')

        qla_max_rates = data.groupby('fSourceName').agg({
            'rate': 'max',
            'fSourceKEY': 'median',
        })
        for source, data in qla_max_rates.iterrows():
            rate = float(data['rate'])
            self.update_qla_data(source, '{:3.1f}'.format(rate))

        significant_qla_max_rates = significant.groupby('fSourceName').agg({
            'rate': 'max',
            'fSourceKEY': 'median',
        })

        for source, data in significant_qla_max_rates.iterrows():
            rate = float(data['rate'])
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

    binned['significance'] = li_ma_significance(
        binned.fNumSigEvts, binned.fNumBgEvts * 5, 0.2
    )

    return binned


def create_mpl_plot(data, outfile=os.path.join(outdir, 'qla.png')):
    alert_rate = create_alert_rate()
    with plt.style.context(('ggplot', )):
        try:
            cycle = plt.rcParams['axes.prop_cycle']
            colors = [style['color'] for style in cycle]
        except KeyError:
            colors = plt.rcParams['axes.color_cycle']
        fig = plt.figure()
        ax_sig = plt.subplot2grid((4, 1), (3, 0))
        ax_rate = plt.subplot2grid(
            (4, 1), (0, 0),
            rowspan=3, sharex=ax_sig
        )
        for (name, group), color in zip(data.groupby('fSourceName'), colors):
            if len(group.index) == 0:
                continue
            ax_rate.errorbar(
                x=group.timeMean.values,
                y=group.rate.values,
                xerr=group.xerr.values,
                yerr=group.yerr.values,
                label=name,
                fmt='o',
                mec='none',
                color=color,
            )

            if name != 'Crab':
                ax_rate.hlines(
                    alert_rate[name],
                    (group.timeMean.values - group.xerr.values).min(),
                    (group.timeMean.values + group.xerr.values).max(),
                    color=color,
                )
            ax_sig.errorbar(
                x=group.timeMean.values,
                y=group.significance.values,
                xerr=group.xerr.values,
                label=name,
                fmt='o',
                mec='none',
                color=color,
            )
        ax_sig.axhline(3, color='darkgray')
        ax_rate.legend(loc='upper left', ncol=4)
        ax_rate.set_ylabel('Excess Event Rate / $\mathrm{h}^{-1}$')
        ax_sig.set_ylabel('$S_{\mathrm{Li/Ma}} \,\, / \,\, \sigma$')
        ymax = max(3.25, np.ceil(ax_sig.get_ylim()[1]))
        ax_sig.set_yticks(np.arange(0, ymax + 0.1, ymax // 4 + 1))
        ax_sig.set_ylim(0, ymax)
        fig.autofmt_xdate()
        fig.tight_layout()
        fig.savefig(outfile)
        plt.close('all')


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


def li_ma_significance(N_on, N_off, alpha=0.2):
    N_on = np.array(N_on, copy=False, ndmin=1)
    N_off = np.array(N_off, copy=False, ndmin=1)

    with np.errstate(divide='ignore', invalid='ignore'):
        p_on = N_on / (N_on + N_off)
        p_off = N_off / (N_on + N_off)

        t1 = N_on * np.log(((1 + alpha) / alpha) * p_on)
        t2 = N_off * np.log((1 + alpha) * p_off)

        ts = (t1 + t2)
        significance = np.sqrt(ts * 2)

    significance[np.isnan(significance)] = 0
    significance[N_on < alpha * N_off] = 0

    return significance
