import logging
from actions.action_charge import ChargeAction
from harnesses.harness_common_utility import ExampleUtility

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def main():
    set_charge()


def set_charge():

    services = ExampleUtility.create_refreshed_services(['SolarConfig', 'Inverter', 'DbForecastDaily', 'DbRadiationHourly'])

    charge_action = ChargeAction()
    charge_action.execute(services)

    ExampleUtility.close_services(services)


if __name__ == "__main__":
    main()
