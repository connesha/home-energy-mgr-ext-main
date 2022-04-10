import datetime
from time import sleep
from config.config import Config
from actions.action_base import ActionBase
from json import dumps
import paho.mqtt.client as mqtt
import asyncio
import logging
from utils.sun_angles import SunAngles


_LOGGER = logging.getLogger(__name__)


class MyeMqttAction(ActionBase):

    def __init__(self):
        super().__init__()
        self.sun_angles = SunAngles(Config.LONGITUDE, Config.LATITUDE)

    def can_execute_now(self, services):
        super().can_execute_now(services)
        # run at lesser frequency at night
        if self.sun_angles.is_daytime(datetime.datetime.now()):
            return self.is_in_last_run_limit_secs(services.get_service("SolarConfig").values.action_freq_secs_mye_mqtt_day)
        else:
            _LOGGER.info("it's nighttime")
            return self.is_in_last_run_limit_secs(services.get_service("SolarConfig").values.action_freq_secs_mye_mqtt_night)

    def execute_impl(self, services):
        super().execute_impl(services)
        _LOGGER.info("execute_impl")

        # get the services that are needed
        myenergi_connection = services.get_service("MyeConnection")

        async def get_eddis() -> None:
            retry_count = 0
            while True:
                try:
                    myenergi_connection.refresh()

                    # build up the dict
                    eddis = await myenergi_connection.client.get_devices("eddi")
                    if eddis is not None and len(eddis) == 1:
                        eddi = eddis[0]
                        _LOGGER.info("Myenergi found EDDI %s" % eddi.serial_number)

                        history_data = await eddi.energy_today()
                        active_heater = eddi.active_heater

                        mqtt_dict = {'eddi_active_heater': active_heater}
                        heater_load = eddi.ct1.power
                        if active_heater == 1:
                            mqtt_dict['eddi_heater1_load'] = heater_load
                            mqtt_dict['eddi_heater2_load'] = 0
                        else:
                            mqtt_dict['eddi_heater1_load'] = 0
                            mqtt_dict['eddi_heater2_load'] = heater_load
                        mqtt_dict['eddi_heater1_today_generated'] = round(history_data["h1d"] + history_data["h1b"], 2)
                        mqtt_dict['eddi_heater2_today_generated'] = round(history_data["h2d"] + history_data["h2b"], 2)
                        # add current time
                        time_str = (datetime.datetime.now()).strftime('%H:%M:%S')
                        mqtt_dict['publish_time'] = time_str

                        # dict to json
                        mqtt_json = dumps(mqtt_dict)
                        # _LOGGER.debug(mqtt_json)

                        # publish to mqtt
                        mqttc = mqtt.Client()
                        mqttc.connect(Config.MQTT_SERVER, Config.MQTT_PORT, Config.MQTT_KEEPALIVE)
                        _LOGGER.debug(f'Connected to MQTT {Config.MQTT_SERVER}:{Config.MQTT_PORT}')
                        mqttc.publish(topic=Config.MQTT_TOPIC_MYENERGI, payload=mqtt_json)

                        # done
                        mqttc.disconnect()

                    else:
                        _LOGGER.error("Myenergi did not find the EDDI. eddis: %s\t" % eddis)

                except Exception as e:
                    _LOGGER.error("Myenergi fail")
                    myenergi_connection.close()
                    if retry_count == 1:
                        _LOGGER.exception("Error connecting to Myenergi. exit")
                        exit(1)
                    else:
                        retry_count += 1
                        _LOGGER.error(f'Error connecting to Myenergi {repr(e)}')
                        _LOGGER.error(f'Retry {retry_count} in 3s')
                        sleep(3)  # wait a bit before retry
                        continue
                break

        loop = asyncio.get_event_loop()
        loop.run_until_complete(get_eddis())
        _LOGGER.info("execute_impl done")


