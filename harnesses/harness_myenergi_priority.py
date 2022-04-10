import logging
from actions.action_mye_priority_switch import MyePriorityAction
from harnesses.harness_common_utility import ExampleUtility


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


if __name__ == '__main__':
    services = ExampleUtility.create_refreshed_services(['SolarConfig', 'Inverter', 'MyeConnection'])

    myenergi_mqtt_action = MyePriorityAction()
    myenergi_mqtt_action.execute(services)

    ExampleUtility.close_services(services)
