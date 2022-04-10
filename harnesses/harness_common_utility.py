from config.config import Config
from services.service_mye_connection import MyeConnection
from services.service_db_forecast_daily import DbForecastDaily
from services.service_inverter import Inverter
from services.service_db_solar_radiation_hourly import DbRadiationHourly
from services.service_solar_config import SolarConfig
from services.services import Services


class ExampleUtility:

    @staticmethod
    def create_refreshed_services(service_names):

        services = Services()

        # instantiate the services
        for service_name in service_names:
            if service_name == 'SolarConfig':
                solar_config = SolarConfig(Config.DB_HOST, Config.DB_DATABASE, Config.DB_USERNAME, Config.DB_PASSWORD)
                services.add_service("SolarConfig", solar_config)
            elif service_name == 'Inverter':
                inverter = Inverter(Config.INVERTER_IP, Config.INVERTER_PORT, Config.INVERTER_SERIAL)
                services.add_service("Inverter", inverter)
            elif service_name == 'MyeConnection':
                myenergi_connection = MyeConnection(Config.MYE_USER, Config.MYE_PASSWORD)
                services.add_service("MyeConnection", myenergi_connection)
            elif service_name == 'DbForecastDaily':
                db_forecast_daily = DbForecastDaily(Config.DB_HOST, Config.DB_DATABASE, Config.DB_USERNAME, Config.DB_PASSWORD)
                services.add_service("DbForecastDaily", db_forecast_daily)
            elif service_name == 'DbRadiationHourly':
                db_radiation_hourly = DbRadiationHourly(Config.DB_HOST, Config.DB_DATABASE, Config.DB_USERNAME, Config.DB_PASSWORD)
                services.add_service("DbRadiationHourly", db_radiation_hourly)

        # refresh
        for service in services:
            service.refresh()

        return services

    @staticmethod
    def close_services(services):
        for service in services:
            service.close()
