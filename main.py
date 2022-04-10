from actions.action_mye_mqtt import MyeMqttAction
from actions.action_mye_priority_switch import MyePriorityAction
from config.config import Config
import datetime
from time import sleep
from actions.action_charge import ChargeAction
from actions.action_forecast import ForecastAction
from actions.action_inverter_mqtt import InverterMqttAction
from actions.action_plot import PlotAction
from actions.action_generation_update import UpdateGenerationAction
from services.service_db_forecast_daily import DbForecastDaily
from services.service_inverter import Inverter
import sys

from services.service_mye_connection import MyeConnection
from services.service_db_solar_radiation_hourly import DbRadiationHourly
from services.service_solar_config import SolarConfig
import logging

from services.services import Services

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

_LOGGER = logging.getLogger(__name__)


def sleep_time_for_hour(sleep_ranges_by_hour, now_hour):
    sleep_secs = sleep_ranges_by_hour[0][1]
    for i in range(len(sleep_ranges_by_hour)):
        range_hour = sleep_ranges_by_hour[i][0]
        if now_hour >= range_hour:
            sleep_secs = sleep_ranges_by_hour[i][1]
        else:
            break
    return sleep_secs


def set_log_level(level_str):
    if level_str == "critical":
        logging.root.setLevel(logging.CRITICAL)
    elif level_str == "error":
        logging.root.setLevel(logging.ERROR)
    elif level_str == "warning":
        logging.root.setLevel(logging.WARNING)
    elif level_str == "info":
        logging.root.setLevel(logging.INFO)
    else:
        logging.root.setLevel(logging.DEBUG)


def main(argv):
    _LOGGER.info("Entered main")
    if len(argv) < 1:
        _LOGGER.error("Needs 1 arg: (1) Path to write plots to")
        exit(1)

    plot_write_path = argv[0]
    _LOGGER.info(f"plot_write_path: {plot_write_path}")

    # instantiate the services
    solar_config = SolarConfig(Config.DB_HOST, Config.DB_DATABASE, Config.DB_USERNAME, Config.DB_PASSWORD)
    inverter = Inverter(Config.INVERTER_IP, Config.INVERTER_PORT, Config.INVERTER_SERIAL)
    myenergi_connection = MyeConnection(Config.MYE_USER, Config.MYE_PASSWORD)
    db_forecast_daily = DbForecastDaily(Config.DB_HOST, Config.DB_DATABASE, Config.DB_USERNAME, Config.DB_PASSWORD)
    db_radiation_hourly = DbRadiationHourly(Config.DB_HOST, Config.DB_DATABASE, Config.DB_USERNAME, Config.DB_PASSWORD)
    # add to the Services container
    services = Services()
    services.add_service("SolarConfig", solar_config)
    services.add_service("Inverter", inverter)
    services.add_service("MyeConnection", myenergi_connection)
    services.add_service("DbForecastDaily", db_forecast_daily)
    services.add_service("DbRadiationHourly", db_radiation_hourly)
    # solar_config is always needed, refresh even before actions
    solar_config.refresh()

    # set the log level according to solar_config
    set_log_level(solar_config.values.log_level)

    # charge action and dependencies
    charge_action = ChargeAction()
    charge_action.add_pre_action(UpdateGenerationAction(UpdateGenerationAction.DAY_YESTERDAY))
    charge_action.add_pre_action(ForecastAction(ForecastAction.TODAY, single_day=True))
    # inverter mqtt action
    inverter_mqtt_action = InverterMqttAction()
    # myenergi mqtt action
    myenergi_mqtt_action = MyeMqttAction()
    # plot action and dependencies
    plot_action = PlotAction(to_file=True, show=False, output_folder=plot_write_path)
    plot_action.add_pre_action(UpdateGenerationAction(UpdateGenerationAction.DAY_TODAY))
    plot_action.add_pre_action(ForecastAction(ForecastAction.TOMORROW, single_day=False))
    # myenergi priority action
    myenergi_priority_action = MyePriorityAction()

    # set the actions to execute
    action_list = [charge_action, inverter_mqtt_action, myenergi_mqtt_action, plot_action, myenergi_priority_action]

    try:
        while True:
            # refresh the services, so will be fresh for the actions
            for service in services:
                service.refresh()

            # set the log level
            solar_config = services.get_service("SolarConfig")
            set_log_level(solar_config.values.log_level)

            # execute all actions that can execute now
            for action in action_list:
                if action.can_execute_now(services):
                    action.execute(services)

            # sleep for a while before going again
            sleep_secs = sleep_time_for_hour(solar_config.values.main_sleep_ranges_by_hour, datetime.datetime.now().hour)
            _LOGGER.debug("Sleeping for %s secs" % sleep_secs)
            sleep(sleep_secs)
    finally:
        for service in services:
            service.close()


if __name__ == "__main__":
    main(sys.argv[1:])
