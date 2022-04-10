import datetime
import logging
from config.config import Config
from actions.action_base import ActionBase
from utils.sun_angles import SunAngles
from utils.utils import Utils

# battery
BATTERY_MIN_WH = 1000
BATTERY_MAX_WH = 5000
BATTERY_CHARGE_VOLTAGE = 52
BATTERY_SOC_TO_WH = int(BATTERY_MAX_WH / 100)
# charging
CHARGE_HOURS = 3
CHARGE_DA_MIN = 0
CHARGE_DA_MAX = 990  # 99 amps, just under the 100a limit
CHARGE_WH_MIN = 1 * BATTERY_CHARGE_VOLTAGE * CHARGE_HOURS  # 1 amp for the full charge time. Yea, it can do under 1 amp, but am not doing that
CHARGE_WH_MAX = BATTERY_MAX_WH - BATTERY_MIN_WH

# when this action can run
EXECUTION_TIME_WINDOW_START = datetime.time(hour=1, minute=45, second=0)
EXECUTION_TIME_WINDOW_END = datetime.time(hour=1, minute=59, second=0)

_LOGGER = logging.getLogger(__name__)


class ChargeAction(ActionBase):

    def __init__(self):
        super().__init__()

    def can_execute_now(self, services):
        super().can_execute_now(services)

        # get the services that are needed
        db_forecast_daily = services.get_service("DbForecastDaily")

        # Are we within the time window
        now_date_time = datetime.datetime.now()
        if Utils.time_in_range(EXECUTION_TIME_WINDOW_START, EXECUTION_TIME_WINDOW_END, now_date_time.time()):
            # yes, it is within the time range
            if self.last_run is not None:
                # we have the last_run date, make sure it was not in this time window
                time_difference = now_date_time - self.last_run
                difference_hours = int(round(time_difference.total_seconds() / 3600))
                if difference_hours >= 20:   # 20 hours is "a long time ago", i.e. well outside any charge-window
                    execute_now = True
                else:
                    execute_now = False
            else:
                # last_run is not set, get status from db
                run_from_db = self.is_charge_set_for_date_from_db(db_forecast_daily, Utils.date_today())
                if run_from_db is True:
                    self.last_run = datetime.datetime.now()
                    execute_now = False
                else:
                    execute_now = True
        else:
            # not within time range
            execute_now = False

        return execute_now

    def execute_impl(self, services):
        super().execute_impl(services)
        _LOGGER.info("execute_impl")

        # get the services that are needed
        solar_config = services.get_service("SolarConfig")
        inverter = services.get_service("Inverter")
        db_forecast_daily = services.get_service("DbForecastDaily")

        # get/set states for use later
        date_today = Utils.date_today()
        time_now = Utils.time_now()
        time_sunrise = self.sunrise_time(date_today)
        time_generation = time_sunrise + datetime.timedelta(minutes=solar_config.values.sunrise_to_real_gen_mins)
        base_load_wh = solar_config.values.usage_base_load_wh
        need_to_charge = False
        wh_charge = 0

        # get today's forecast
        forecast_wh = db_forecast_daily.get_forecast_wh(date_today)
        _LOGGER.info("forecast_wh: %s" % forecast_wh)

        # what is current battery level
        battery_level_wh = inverter.get_battery_capacity_soc() * BATTERY_SOC_TO_WH
        battery_level_usable_wh = Utils.clamp_value(battery_level_wh - BATTERY_MIN_WH, 0, BATTERY_MAX_WH)
        _LOGGER.info("battery_level_usable_wh: %s" % battery_level_usable_wh)

        # calculate if need to charge, and if so by how much
        _LOGGER.info("usage_daily_wh: %s" % solar_config.values.usage_daily_wh)
        if forecast_wh < (solar_config.values.usage_daily_wh - battery_level_usable_wh):
            # won't have enough generation to get through the day, so will need to charge
            needed_for_day_wh = solar_config.values.usage_daily_wh - forecast_wh - battery_level_usable_wh
            wh_charge = Utils.clamp_value(needed_for_day_wh, 0, BATTERY_MAX_WH - battery_level_wh)
            need_to_charge = True
            _LOGGER.info("not enough for day. wh_charge: %s" % wh_charge)
        else:
            # is there enough to get to when generation starts
            _LOGGER.info("time_generation: %s\t is %s mins after sunrise" % (time_generation, solar_config.values.sunrise_to_real_gen_mins))
            needed_from_now_to_generation_wh = self.wh_consumed_between_times(time_now, time_generation, base_load_wh)
            # TODO: use the hourly radiation to predict morning gen, and calculate if have enough for breakfast usage
            _LOGGER.info("needed_from_now_to_generation_wh: %s" % needed_from_now_to_generation_wh)
            if battery_level_usable_wh < needed_from_now_to_generation_wh:
                # don't have enough to get to generation time. Need to charge
                need_to_charge = True
                # how much is needed: minus the time we're actually charging (this time has no battery consumption)
                wh_charge = needed_from_now_to_generation_wh - battery_level_usable_wh - (
                        CHARGE_HOURS * base_load_wh)
                # wh_charge number could be negative, so make it 0 or positive
                wh_charge = Utils.clamp_value(wh_charge, 0, CHARGE_WH_MAX)
                _LOGGER.info("not enough for morning. wh_charge: %s" % wh_charge)
            else:
                _LOGGER.info("have enough")

        # set inverter and save to db
        if need_to_charge:
            # doubly ensure within safety ranges
            wh_charge = Utils.clamp_value(wh_charge, 0, CHARGE_WH_MAX)
            # set 1 amp as the minimum (10 da).
            if wh_charge < CHARGE_WH_MIN:
                wh_charge = 0 if wh_charge < (CHARGE_WH_MIN/2) else CHARGE_WH_MIN
            deci_amp_needed = self.set_charge(inverter, wh_charge)
            db_forecast_daily.update_charge(date_today, battery_level_wh, True, wh_charge, deci_amp_needed)
        else:
            inverter.charging_turn_off()
            db_forecast_daily.update_charge(date_today, battery_level_wh, False)

        #  all done, commit
        db_forecast_daily.commit()
        _LOGGER.info("execute_impl done")

    def set_charge(self, inverter, wh_needed):
        # convert to deciAmps
        deci_amp_needed = self.wh_to_deciamp(wh_needed)
        # safety yet again - make sure is in range
        deci_amp_needed = Utils.clamp_value(deci_amp_needed, CHARGE_DA_MIN, CHARGE_DA_MAX)
        # set on inverter
        inverter.set_charge_rate(deci_amp_needed)
        _LOGGER.info("set_charge_rate: %s" % deci_amp_needed)
        return deci_amp_needed

    def wh_to_deciamp(self, wh_needed):
        watts_per_hour_needed = wh_needed / CHARGE_HOURS
        current_needed = watts_per_hour_needed / BATTERY_CHARGE_VOLTAGE
        deci_current_needed = int(round(current_needed * 10))
        return deci_current_needed

    def wh_consumed_between_times(self, start_time, end_time, base_load):
        duration = end_time - start_time
        duration_mins = int(round(duration.total_seconds() / 60))
        load_per_min = base_load / 60
        wh_consumed = int(round(duration_mins * load_per_min))
        return wh_consumed

    def sunrise_time(self, date):
        sun_angles = SunAngles(Config.LONGITUDE, Config.LATITUDE)
        sunrise = sun_angles.get_sunrise_for_date(date)
        sunrise = sunrise.replace(tzinfo=None)
        return sunrise

    def is_charge_set_for_date_from_db(self, db_forecast_daily, date):
        is_charge_set = db_forecast_daily.is_charge_set_for_date(date)
        return is_charge_set
