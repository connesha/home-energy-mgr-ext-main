import logging
from abc import ABC
from config.config import Config
from actions.action_base import ActionBase
from utils.sun_angles import SunAngles
from utils.utils import Utils
from utils.weather_forecast import WeatherForecast

_LOGGER = logging.getLogger(__name__)


class ForecastAction(ActionBase, ABC):
    TODAY = 0
    TOMORROW = 1
    DELAY_BETWEEN_EXECUTIONS_SECS = 5 * 60

    def __init__(self, start_day, single_day=True):
        super().__init__()
        self.start_day = start_day
        self.single_day = single_day

    def can_execute_now(self, services):
        super().can_execute_now(services)
        return self.is_in_last_run_limit_secs(self.DELAY_BETWEEN_EXECUTIONS_SECS)

    def execute_impl(self, services):
        super().execute_impl(services)
        _LOGGER.info("execute_impl")

        # get the services that are needed
        solar_config = services.get_service("SolarConfig")
        db_forecast_daily = services.get_service("DbForecastDaily")
        db_rad_hourly = services.get_service("DbRadiationHourly")

        # forecast
        if self.single_day:
            num_days = 1
        else:
            num_days = solar_config.values.forecast_num_days_future
        self.forecast(solar_config, db_forecast_daily, db_rad_hourly, Utils.date_from_date_offset(Utils.date_today(), self.start_day), num_days)
        _LOGGER.info("execute_impl done")

    def forecast(self, solar_config, db_forecast_daily, db_rad_hourly, start_date, num_days=1):
        weather_forecast = WeatherForecast()
        weather_forecast.load_weather_data()
        sun_angles = SunAngles(Config.LONGITUDE, Config.LATITUDE)

        # use the same number days for every one
        num_days_history = sun_angles.get_bounded_num_days_back_within_angle(solar_config.values.forecast_sun_angle_max,
                                                                             solar_config.values.forecast_num_days_history_min,
                                                                             solar_config.values.forecast_num_days_history_max)
        _LOGGER.info("Using %s days history" % num_days_history)

        for i in range(0, num_days):
            date = Utils.date_from_date_offset(start_date, i)
            radiation = weather_forecast.get_radiation_for_date_total(date)
            forecast_factor = db_forecast_daily.get_actual_factor_sum_similar_radiation(
                Utils.date_yesterday(), num_days_history, radiation, solar_config.values.forecast_num_days_use)
            forecast_wh = int(round(radiation * forecast_factor))
            db_forecast_daily.insert_or_update_forecast(date, radiation, forecast_factor, forecast_wh)
            hourly_radiation = weather_forecast.get_radiation_for_date_hourly(date)
            db_rad_hourly.insert_or_update_radiations(date, hourly_radiation)

        db_forecast_daily.commit()
        db_rad_hourly.commit()
