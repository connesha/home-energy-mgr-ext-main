import logging
from actions.action_mye_mqtt import MyeMqttAction
from time import sleep
from harnesses.harness_common_utility import ExampleUtility

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


if __name__ == '__main__':
    services = ExampleUtility.create_refreshed_services(['SolarConfig', 'Inverter', 'MyeConnection'])

    action = MyeMqttAction()
    for x in range(0, 5):
        action.execute(services)
        sleep(10)

    ExampleUtility.close_services(services)
