import logging
from datetime import timedelta, datetime
import pandas as pd


from custos import IntervalCheck

from . import retry_smart_fact_crawler as sfc
from .message_mixin import MessageMixin
from . import conditions

log = logging.getLogger(__name__)

CATEGORY_SHIFTER = 'shifter'
CATEGORY_DEVELOPER = 'developer'

class MainJsStatusCheck(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_mainjs_not_running
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)


class WindSpeedCheck(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_high_windspeed,
            conditions.is_not_parked,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)


class WindGustCheck(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_high_windgusts,
            conditions.is_not_parked,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)


class MedianCurrentCheck(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_median_current_high,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)


class MaximumCurrentCheck(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_maximum_current_high,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)


class RelativeCameraTemperatureCheck(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_rel_camera_temperature_high,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)


class BiasNotOperatingDuringDataRun(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_bias_not_operating,
            conditions.is_data_run,
            conditions.is_data_taking,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)

class BiasChannelsInOverCurrent(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_overcurrent,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)


class BiasVoltageNotAtReference(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_bias_voltage_not_at_reference,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)


class ContainerTooWarm(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_container_too_warm,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)



class DriveInErrorDuringDataRun(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_drive_error,
            conditions.is_data_run,
            conditions.is_data_taking,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)


class BiasVoltageOnButNotCalibrated(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_voltage_on,
            conditions.is_feedback_not_calibrated,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)


class DIMNetworkNotAvailable(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_dim_network_down,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)


class NoDimCtrlServerAvailable(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_no_dimctrl_server_available,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)




class TriggerRateLowForTenMinutes(IntervalCheck, MessageMixin):
    history = pd.DataFrame()

    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_data_taking,
            self.is_trigger_rate_low_for_ten_minutes,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)

    def is_trigger_rate_low_for_ten_minutes(self):
        '''Trigger rate < 1/s for 10 minutes'''
        current_trigger_rate = sfc.trigger_rate().trigger_rate.value
        self._append_to_history(current_trigger_rate)
        self._remove_old_entries()
        df = pd.DataFrame(self.history)
        return not df.empty and (df.rate < 1).all()

    def _append_to_history(self, rate):
        self.history = self.history.append([{'timestamp': datetime.utcnow(), 'rate': rate}])

    def _remove_old_entries(self):
        now = datetime.utcnow()
        self.history = self.history[(now - self.history.timestamp) < timedelta(minutes=10)]


class IsUserAwakeBeforeShutdown(IntervalCheck, MessageMixin):
    '''
    This Check should find out if the user is actually awake some time before
    the scheduled shutdown.

    In order to find out, if the shifter is awake, we need to find out:
      * Is it 20minutes (or less) before shutdown?
      * Who is the current shifter (username)?
      * Is she awake, i.e. did he press the "I am awake button" recently?
    '''
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_20minutes_or_less_before_shutdown,
            conditions.is_nobody_awake,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_SHIFTER)




class ShifterOnShift(IntervalCheck, MessageMixin):
    def check(self):
        checklist = [
            conditions.is_shift_at_the_moment,
            conditions.is_nobody_on_shift,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_DEVELOPER)


class ParkingChecklistFilled(IntervalCheck, MessageMixin):
    '''
    This Check should find out if the parking/shutdown checklist
    was filled, i.e. "if the shutdown checked by a person"
    within a certain time after the scheduled shutdown.
    '''
    def check(self):
        checklist = [
            conditions.is_no_shift_at_the_moment,
            conditions.is_last_shutdown_already_10min_past,
            conditions.is_checklist_not_filled,
        ]
        if all(f() for f in checklist):
            self.message(checklist, category=CATEGORY_DEVELOPER)


class FlareAlert(IntervalCheck, MessageMixin):
    max_rate = defaultdict(lambda: 0)

    def check(self):
        data = get_data()
        if data is None:
            return
        if len(data.index) == 0:
            return

        create_mpl_plot(data)

        significance_cut = 3 # sigma
        significant = data[data.significance >= significance_cut]

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

