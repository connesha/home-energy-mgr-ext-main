import logging
from unittest import TestCase

from config.config import Config
from services.services import Services

from services.service_db_forecast_daily import DbForecastDaily
from services.service_inverter import Inverter
from services.service_solar_config import SolarConfig

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


class TestChargeAction(TestCase):
    def test_services(self):
        services = Services()

        solar_config = SolarConfig(Config.DB_HOST, Config.DB_DATABASE, Config.DB_USERNAME, Config.DB_PASSWORD)
        db_forecast_daily = DbForecastDaily(Config.DB_HOST, Config.DB_DATABASE, Config.DB_USERNAME, Config.DB_PASSWORD)
        inverter = Inverter(Config.INVERTER_IP, Config.INVERTER_PORT, Config.INVERTER_SERIAL)

        services.add_service("SolarConfig", solar_config)
        services.add_service("DbForecastDaily", db_forecast_daily)
        services.add_service("Inverter", inverter)

        for service in services:
            print(service)

        print(services)

