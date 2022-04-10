import logging
from datetime import datetime, timedelta
from unittest import TestCase, mock
from actions.action_charge import ChargeAction
from unittest.mock import create_autospec

from config.config import Config

from services.service_db_forecast_daily import DbForecastDaily
from services.service_inverter import Inverter
from services.service_solar_config import SolarConfig
from services.services import Services

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


# noinspection PyUnusedLocal,PyShadowingNames
class TestChargeAction(TestCase):
    def test_wh_consumed_between_times(self):
        charge_action = self.create_charge_action()
        start_time = datetime.now()

        end_time = start_time + timedelta(hours=3, minutes=30)
        wh_consumed = charge_action.wh_consumed_between_times(start_time, end_time, 100)
        self.assertEqual(wh_consumed, 350)

        end_time = start_time + timedelta(hours=1, minutes=15)
        wh_consumed = charge_action.wh_consumed_between_times(start_time, end_time, 100)
        self.assertEqual(wh_consumed, 125)

        end_time = start_time + timedelta(hours=9, minutes=45)
        wh_consumed = charge_action.wh_consumed_between_times(start_time, end_time, 200)
        self.assertEqual(wh_consumed, (9 * 200) + 150)

    @mock.patch('utils.utils.Utils.time_now')
    def test_execute(self, mock_time_now):
        mock_time_now.return_value = datetime.now().replace(hour=1, minute=45)

        mock_inverter = self.create_mock_inverter()
        # mock_db_forecast_daily = self.create_mock_db_forecast_daily()
        # mock_config = self.create_mock_solar_config()

        solar_config = SolarConfig(Config.DB_HOST, Config.DB_DATABASE, Config.DB_USERNAME, Config.DB_PASSWORD)
        db_forecast_daily = DbForecastDaily(Config.DB_HOST, Config.DB_DATABASE, Config.DB_USERNAME, Config.DB_PASSWORD)
        services = Services()
        services.add_service("SolarConfig", solar_config)
        services.add_service("DbForecastDaily", db_forecast_daily)
        for service in services:
            service.refresh()

        charge_action = self.create_charge_action()
        # charge_action.add_pre_action(ForecastAction(ForecastAction.TODAY, 1))
        charge_action.execute(services)

    def create_charge_action(self):
        charge_action = ChargeAction()
        return charge_action

    def create_mock_inverter(self):
        mock = create_autospec(Inverter)
        mock.get_battery_capacity_soc.return_value = 39
        return mock

    def create_mock_db_forecast_daily(self):
        mock = create_autospec(DbForecastDaily)
        mock.get_forecast_wh.return_value = 16000
        return mock

    def create_mock_solar_config(self):
        mock = create_autospec(SolarConfig)
        mock.usage_base_load_wh.return_value = 175
        mock.usage_daily_wh.return_value = 17000
        return mock

