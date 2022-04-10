import datetime
from time import sleep
from actions.action_base import ActionBase
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

# TODO: this is just out of interest, and to start using the MYE API a bit more. This can be done better in HA/NodeRed


class MyePriorityAction(ActionBase):

    def __init__(self):
        super().__init__()
        self.battery_greater_rule_ran = False
        self.battery_less_rule_ran = False
        self.time_rules_ran = []
        self._reset_rules_ran()
        self.last_executed_hour = None

    def can_execute_now(self, services):
        super().can_execute_now(services)

        return self.is_in_last_run_limit_secs(services.get_service("SolarConfig").values.action_freq_secs_mye_priority)

    def execute_impl(self, services):
        super().execute_impl(services)
        _LOGGER.info("execute_impl")

        # get the services that are needed
        solar_config = services.get_service("SolarConfig")
        inverter = services.get_service("Inverter")
        myenergi_connection = services.get_service("MyeConnection")

        # generic info, needed many times later
        current_hour = datetime.datetime.now().hour
        current_hour_str = "%s" % current_hour
        current_battery_soc = inverter.get_battery_capacity_soc()

        # see if its time to reset. Reset at midnight
        if self.last_executed_hour is not None:
            if current_hour < self.last_executed_hour:
                self._reset_rules_ran()
        self.last_executed_hour = current_hour

        # load rules
        eddi_priority_switch_rules = solar_config.values.eddi_priority_switch_rules
        time_rules_dict = {}
        battery_greater_level = None
        battery_greater_priority = None
        battery_less_level = None
        battery_less_priority = None
        for rule, priority in eddi_priority_switch_rules:
            if rule.startswith("time=="):
                hour_int = rule.split("time==", 1)[1]
                priority_int = int(priority)
                time_rules_dict[hour_int] = priority_int
            elif rule.startswith("battery>"):
                battery_greater_level = int(rule.split("battery>", 1)[1])
                battery_greater_priority = int(priority)
            elif rule.startswith("battery<"):
                battery_less_level = int(rule.split("battery<", 1)[1])
                battery_less_priority = int(priority)
            else:
                _LOGGER.error("invalid rule type %s" % rule)
        _LOGGER.debug("loaded %s time rules" % len(time_rules_dict))

        # execute rules
        if current_hour_str in time_rules_dict:
            # time based rule
            if current_hour not in self.time_rules_ran:
                _LOGGER.info("run rule time for hour %s" % current_hour_str)
                priority_to_set = int(time_rules_dict[current_hour_str])
                self.set_heater_priority(myenergi_connection, priority_to_set)
                self.time_rules_ran.append(current_hour)
            else:
                _LOGGER.info("Already ran time rule for hour %s" % current_hour_str)
        elif battery_greater_level is not None and self.battery_greater_rule_ran is False:
            # battery_greater_level
            if current_battery_soc > battery_greater_level:
                _LOGGER.info("run battery_greater_level. current: %s  rule: %s" % (current_battery_soc, battery_greater_level))
                self.set_heater_priority(myenergi_connection, battery_greater_priority)
                self.battery_greater_rule_ran = True
        elif battery_less_level is not None and self.battery_less_rule_ran is False:
            # battery_less_level
            if current_battery_soc < battery_greater_level:
                _LOGGER.info("run battery_less_level. current: %s  rule: %s" % (current_battery_soc, battery_less_level))
                self.set_heater_priority(myenergi_connection, battery_less_priority)
                self.battery_less_rule_ran = True
        else:
            _LOGGER.debug("No rule to run now")

        _LOGGER.info("execute_impl done")

    def _reset_rules_ran(self):
        _LOGGER.info("reset rules")
        self.battery_greater_rule_ran = False
        self.battery_less_rule_ran = False
        self.time_rules_ran = []

    def set_heater_priority(self, myenergi_connection, priority_to_set):
        async def set_heater_priority_async():
            retry_count = 0
            while True:
                try:
                    myenergi_connection.refresh()

                    # set priority
                    eddis = await myenergi_connection.client.get_devices("eddi")
                    if eddis is not None and len(eddis) == 1:
                        eddi = eddis[0]
                        tmp_prio = eddi.priority
                        _LOGGER.info("rule mp_prio: %s" % tmp_prio)
                        current_heater_priority = int(eddi.heater_priority)
                        _LOGGER.info("rule current_heater_priority: %s \t priority_to_set: %s" % (current_heater_priority, priority_to_set))
                        if current_heater_priority != priority_to_set:
                            ret_val = await eddi.set_heater_priority("heater%s" % priority_to_set)
                            _LOGGER.info("rule ret_val: %s" % ret_val)
                            if ret_val is not True:
                                raise Exception("eddi.set_priority: %s" % ret_val)
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
        loop.run_until_complete(set_heater_priority_async())
        _LOGGER.info("execute_impl done")

