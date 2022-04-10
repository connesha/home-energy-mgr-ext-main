import logging
from actions.action_base import ActionBase
from utils.utils import Utils

_LOGGER = logging.getLogger(__name__)


class UpdateGenerationAction(ActionBase):
    DAY_TODAY = 0
    DAY_YESTERDAY = -1

    def __init__(self, day=DAY_TODAY, override_value=None):
        super().__init__()
        self.day = day
        self.override_value = override_value
        # verify args within ranges, for safety of not overwriting DB
        if not (self.day == UpdateGenerationAction.DAY_TODAY or self.day == UpdateGenerationAction.DAY_YESTERDAY):
            raise Exception("UpdateGenerationAction: Day must be DAY_TODAY or DAY_YESTERDAY")
        if self.override_value is not None and self.day != UpdateGenerationAction.DAY_TODAY:
            raise Exception("UpdateGenerationAction: Can only override DAY_TODAY")

    def can_execute_now(self, services):
        super().can_execute_now(services)
        # always execute
        return True

    def execute_impl(self, services):
        super().execute_impl(services)
        _LOGGER.info("execute_impl")

        # get the services that are needed
        inverter = services.get_service("Inverter")
        db_forecast_daily = services.get_service("DbForecastDaily")
        solar_config = services.get_service("SolarConfig")

        # what generated_wh
        if self.override_value is not None:
            generated_wh = self.override_value
            date_to_update = Utils.date_today()
        elif self.day == UpdateGenerationAction.DAY_TODAY:
            if solar_config.values.update_gen_today == 0:
                generated_wh = "NULL"
                _LOGGER.info("update_gen_today NULL")
            else:
                generated_wh = inverter.get_today_generated() * 100
            date_to_update = Utils.date_today()
        elif self.day == UpdateGenerationAction.DAY_YESTERDAY:
            generated_wh = inverter.get_today_generated() * 100
            date_to_update = Utils.date_tomorrow()
        else:
            raise Exception("UpdateGenerationAction: invalid state")

        # store in db
        db_forecast_daily.update_actual_wh(date_to_update, generated_wh)
        db_forecast_daily.commit()
        _LOGGER.info("execute_impl done")
