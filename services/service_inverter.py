import logging
import umodbus
import umodbus.exceptions
import pysolarmanv5.registers as registers
from sys import exit
from time import strptime, mktime, sleep
from pysolarmanv5.pysolarmanv5 import PySolarmanV5, V5FrameError
from services.service_base import ServiceBase

HR_CHARGE_LEVEL_ENABLE = 43110
HR_CHARGE_CURRENT_DECI = 43141
HR_CHARGE_TIME_START_HOUR = 43143
HR_CHARGE_TIME_START_MIN = 43144
HR_CHARGE_TIME_END_HOUR = 43145
HR_CHARGE_TIME_END_MIN = 43146

HR_VAL_CHARGE_LEVEL_ENABLE_STOP = 33
HR_VAL_CHARGE_LEVEL_ENABLE_RUN = 35

_LOGGER = logging.getLogger(__name__)


class Inverter(ServiceBase):

    def __init__(self, host, port, serial, modified_metrics=True, verbose=0):
        super().__init__()
        self.host = host
        self.port = port
        self.serial = serial
        self.verbose = verbose
        self.modified_metrics = modified_metrics
        self.metrics_dict = {}
        self.custom_metrics_dict = {}
        self.modbus = None
        return

    def refresh(self):
        super().refresh()
        self._clear_state()
        self._read_data()
        return

    def close(self):
        super().close()
        self._clear_state()
        return

    # noinspection PyBroadException
    def _read_data(self):
        regs_ignored = 0
        try:
            _LOGGER.debug('Connecting to Solis Modbus')
            self.modbus = PySolarmanV5(self.host, self.serial, port=self.port, mb_slave_id=1, verbose=self.verbose)
        except Exception:
            _LOGGER.exception("Exception connecting to Solis Modbus")
            exit(1)

        _LOGGER.debug('Scraping...')

        for r in registers.all_regs:
            regs = []
            reg = r[0]
            reg_len = len(r[1])
            reg_des = r[1]

            # Sometimes the query fails this will retry 3 times before exiting
            c = 0
            while True:
                try:
                    # _LOGGER.debug(f'Scrapping registers {reg} length {reg_len}')
                    # read registers at address , store result in regs list
                    regs = self.modbus.read_input_registers(register_addr=reg, quantity=reg_len)
                    # _LOGGER.debug(regs)
                except Exception as e:
                    if c == 3:
                        _LOGGER.error(
                            f'Cannot read registers {reg} length{reg_len}. Tried {c} times. Exiting {repr(e)}')
                        exit(1)
                    else:
                        c += 1
                        _LOGGER.warning(f'Cannot read registers {reg} length {reg_len} {repr(e)}')
                        _LOGGER.warning(f'Retry {c} in 3s')
                        sleep(3)  # hold before retry
                        continue
                break

            # Convert time to epoch
            if reg == 33022:
                inv_year = '20' + str(regs[0]) + '-'
                if regs[1] < 10:
                    inv_month = '0' + str(regs[1]) + '-'
                else:
                    inv_month = str(regs[1]) + '-'
                if regs[2] < 10:
                    inv_day = '0' + str(regs[2]) + ' '
                else:
                    inv_day = str(regs[2]) + ' '
                if regs[3] < 10:
                    inv_hour = '0' + str(regs[3]) + ':'
                else:
                    inv_hour = str(regs[3]) + ':'
                if regs[4] < 10:
                    inv_min = '0' + str(regs[4]) + ':'
                else:
                    inv_min = str(regs[4]) + ':'
                if regs[5] < 10:
                    inv_sec = '0' + str(regs[5])
                else:
                    inv_sec = str(regs[5])
                inv_time = inv_year + inv_month + inv_day + inv_hour + inv_min + inv_sec
                _LOGGER.debug(f'Solis Inverter time: {inv_time}')
                time_tuple = strptime(inv_time, '%Y-%m-%d %H:%M:%S')
                time_epoch = mktime(time_tuple)
                self.metrics_dict['system_epoch'] = 'System Epoch Time', time_epoch
                self.metrics_dict['inverter_time'] = 'Inverter Time', inv_time

            # Add metric to list

            for (i, item) in enumerate(regs):
                if '*' not in reg_des[i][0]:
                    self.metrics_dict[reg_des[i][0]] = reg_des[i][1], item

                    # Add custom metrics to custom_metrics_dict
                    # Get battery metric for modification
                    if reg_des[i][0] == 'battery_power_2':
                        self.custom_metrics_dict[reg_des[i][0]] = item
                    elif reg_des[i][0] == 'battery_current_direction':
                        self.custom_metrics_dict[reg_des[i][0]] = item

                    # Get grid metric for modification
                    elif reg_des[i][0] == 'meter_active_power_1':
                        self.custom_metrics_dict[reg_des[i][0]] = item
                    elif reg_des[i][0] == 'meter_active_power_2':
                        self.custom_metrics_dict[reg_des[i][0]] = item

                    # Get load metric for modification
                    elif reg_des[i][0] == 'house_load_power':
                        self.custom_metrics_dict[reg_des[i][0]] = item
                    elif reg_des[i][0] == 'total_dc_input_power_2':
                        self.custom_metrics_dict[reg_des[i][0]] = item
                    elif reg_des[i][0] == 'bypass_load_power':
                        self.custom_metrics_dict[reg_des[i][0]] = item

                else:
                    regs_ignored += 1

        # _LOGGER.debug(f'Ignored registers: {regs_ignored}')

        # Create modified metrics
        if self.modified_metrics:
            self._add_modified_metrics(self.custom_metrics_dict)

        _LOGGER.debug('Scraped')

    def _clear_state(self):
        self.metrics_dict = {}
        self.custom_metrics_dict = {}
        self.modbus = None

    def _add_modified_metrics(self, custom_metrics_dict):
        met_pwr = custom_metrics_dict['meter_active_power_1'] - custom_metrics_dict['meter_active_power_2']
        total_load = custom_metrics_dict['house_load_power'] + custom_metrics_dict['bypass_load_power']

        # Present battery modified metrics
        if custom_metrics_dict['battery_current_direction'] == 0:
            self.metrics_dict['battery_power_modified'] = 'Battery Power(modified)', custom_metrics_dict['battery_power_2']
            self.metrics_dict['battery_power_in_modified'] = 'Battery Power In(modified)', custom_metrics_dict['battery_power_2']
            self.metrics_dict['battery_power_out_modified'] = 'Battery Power Out(modified)', 0
            self.metrics_dict['grid_to_battery_power_in_modified'] = 'Grid to Battery Power In(modified)', 0
        else:
            self.metrics_dict['battery_power_modified'] = 'Battery Power(modified)', custom_metrics_dict['battery_power_2'] * -1  # negative
            self.metrics_dict['battery_power_out_modified'] = 'Battery Power Out(modified)', custom_metrics_dict['battery_power_2']
            self.metrics_dict['battery_power_in_modified'] = 'Battery Power In(modified)', 0
            self.metrics_dict['grid_to_battery_power_in_modified'] = 'Grid to Battery Power In(modified)', 0

        if total_load < met_pwr and custom_metrics_dict['battery_power_2'] > 0:
            self.metrics_dict['grid_to_battery_power_in_modified'] = 'Grid to Battery Power In(modified)', custom_metrics_dict['battery_power_2']

        # Present meter modified metrics
        if met_pwr > 0:
            self.metrics_dict['meter_power_in_modified'] = 'Meter Power In(modified)', met_pwr
            self.metrics_dict['meter_power_modified'] = 'Meter Power(modified)', met_pwr
            self.metrics_dict['meter_power_out_modified'] = 'Meter Power Out(modified)', 0
        else:
            self.metrics_dict['meter_power_out_modified'] = 'Meter Power Out(modified)', met_pwr * - 1  # negative
            self.metrics_dict['meter_power_in_modified'] = 'Meter Power In(modified)', 0
            self.metrics_dict['meter_power_modified'] = 'Meter Power(modified)', met_pwr

        # Present load modified metrics
        self.metrics_dict['total_load_power_modified'] = 'Total Load Power(modified)', total_load

        if 0 < custom_metrics_dict['total_dc_input_power_2'] <= total_load:
            self.metrics_dict['solar_to_house_power_modified'] = 'Solar To House Power(modified)', custom_metrics_dict['total_dc_input_power_2']
        elif custom_metrics_dict['total_dc_input_power_2'] == 0:
            self.metrics_dict['solar_to_house_power_modified'] = 'Solar To House Power(modified)', 0
        elif custom_metrics_dict['total_dc_input_power_2'] > total_load:
            self.metrics_dict['solar_to_house_power_modified'] = 'Solar To House Power(modified)', total_load

        # _LOGGER.debug('Added modified metrics')

    def get_battery_capacity_soc(self):
        return self.metrics_dict['battery_capacity_soc'][1]

    def get_today_generated(self):
        return self.metrics_dict['today_generated'][1]

    def get_yesterday_generated(self):
        return self.metrics_dict['yesterday_generated'][1]

    def charging_turn_on(self):
        _LOGGER.info("Turn On Charging")
        read_val = self._scan_holding_register(HR_CHARGE_LEVEL_ENABLE)
        if read_val != HR_VAL_CHARGE_LEVEL_ENABLE_RUN:
            _LOGGER.info("Turning On Charging")
            self._write_holding_register(HR_CHARGE_LEVEL_ENABLE, HR_VAL_CHARGE_LEVEL_ENABLE_RUN)
            self._scan_holding_register(HR_CHARGE_LEVEL_ENABLE)
        return

    def charging_turn_off(self):
        _LOGGER.info("Turn Off Charging")
        read_val = self._scan_holding_register(HR_CHARGE_LEVEL_ENABLE)
        if read_val != HR_VAL_CHARGE_LEVEL_ENABLE_STOP:
            _LOGGER.info("Turning Off Charging")
            self._write_holding_register(HR_CHARGE_LEVEL_ENABLE, HR_VAL_CHARGE_LEVEL_ENABLE_STOP)
            self._scan_holding_register(HR_CHARGE_LEVEL_ENABLE)
        return

    def set_charge_rate(self, current_da):
        self.charging_turn_on()
        self._write_holding_register(HR_CHARGE_CURRENT_DECI, current_da)
        read_val = self._scan_holding_register(HR_CHARGE_CURRENT_DECI)
        if read_val == current_da:
            _LOGGER.info(f"Set Charge rate:\t {current_da} dA")
        else:
            _LOGGER.error(f"Error setting charge rate:  {current_da} != {read_val}")

        return

    def _scan_holding_registers(self, range_start, range_end):
        for x in range(range_start, range_end):
            self._scan_holding_register(x)
        return

    def _scan_holding_register(self, register):
        try:
            val = self.modbus.read_holding_registers(register_addr=register, quantity=1)[0]
            return val
        except (V5FrameError, umodbus.exceptions.IllegalDataAddressError):
            pass

    # noinspection PyBroadException,PyPep8
    def _write_holding_register(self, register, new_value):
        try:
            self.modbus.write_holding_register(register_addr=register, value=new_value)
        except (V5FrameError, umodbus.exceptions.IllegalDataAddressError):
            pass
        return

