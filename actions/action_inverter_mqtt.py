import datetime
from json import dumps
import logging
import paho.mqtt.client as mqtt
from config.config import Config
from actions.action_base import ActionBase

_LOGGER = logging.getLogger(__name__)


class InverterMqttAction(ActionBase):

    def __init__(self):
        super().__init__()

    def can_execute_now(self, services):
        super().can_execute_now(services)
        # always run
        return True

    # noinspection PyBroadException
    def execute_impl(self, services):
        _LOGGER.info("execute_impl")
        super().execute_impl(services)

        # get the services that are needed
        inverter = services.get_service("Inverter")

        mqtt_dict = {}
        try:
            # Resize dictionary and convert to JSON
            for metric, value in inverter.metrics_dict.items():
                mqtt_dict[metric] = value[1]
            time_str = (datetime.datetime.now()).strftime('%H:%M:%S')
            mqtt_dict['publish_time'] = time_str

            mqtt_json = dumps(mqtt_dict)

            mqttc = mqtt.Client()
            mqttc.connect(Config.MQTT_SERVER, Config.MQTT_PORT, Config.MQTT_KEEPALIVE)
            _LOGGER.debug(f'Connected to MQTT {Config.MQTT_SERVER}:{Config.MQTT_PORT}')

            mqttc.publish(topic=Config.MQTT_TOPIC_INVERTER, payload=mqtt_json)
            mqttc.disconnect()
            _LOGGER.debug(f'Published to MQTT. len(mqtt_json): {len(mqtt_json)}')

        except Exception:
            _LOGGER.exception('Could not connect to MQTT')

        _LOGGER.info("execute_impl done")

