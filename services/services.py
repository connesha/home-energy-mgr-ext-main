
class ServicesIterator:
    def __init__(self, services):
        self.services = services
        self._index = 0

    def __next__(self):
        if self._index < len(self.services.services_dict):
            self._index += 1
            dict_key = list(self.services.services_dict)[self._index - 1]
            dict_val = self.services.services_dict[dict_key]
            return dict_val
        else:
            raise StopIteration


class Services:
    TYPE_SOLAR_CONFIG = "solar_config"
    TYPE_INVERTER = "inverter"
    TYPE_MYENERGI = "myenergi"
    TYPE_DB_SOLAR_FORECASTS = "db_solar_forecasts"
    TYPE_DB_SOLAR_RADIATION_HOURLY = "db_solar_radiation_hourly"

    def __init__(self):
        self.services_dict = {}

    def __iter__(self):
        return ServicesIterator(self)

    def add_service(self, service_type, service):
        self.services_dict[service_type] = service

    def get_service(self, service_type):
        return self.services_dict[service_type]
