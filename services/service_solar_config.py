import logging

from services.service_base import ServiceBase
from services.db_properties import DbProperties

_DB_TABLE = "solar_config"

_LOGGER = logging.getLogger(__name__)


class SolarConfig(DbProperties, ServiceBase):

    def __init__(self, host, database, user, password):
        DbProperties.__init__(self, host, database, _DB_TABLE, user, password)
        ServiceBase.__init__(self)
        return

    # TODO: this refresh and reload with is getting confusing with multiple inheritance. It works, but could be nicer
    def refresh(self):
        super().refresh()
        self.reload()
        return

    def close(self):
        DbProperties.close(self)
        ServiceBase.close(self)

    def reload(self):
        self.close()  # TODO: would prefer not to close each time, but the queries are being cached. Need to look into it, closing for now
        self._connect_if_necessary()
        value_dict = self._read_properties()
        if value_dict["away_mode"] == "on":
            value_dict["usage_daily_wh"] = value_dict["away_usage_daily_wh"]
            value_dict["usage_base_load_wh"] = value_dict["away_usage_base_load_wh"]
        else:
            value_dict["usage_daily_wh"] = value_dict["home_usage_daily_wh"]
            value_dict["usage_base_load_wh"] = value_dict["home_usage_base_load_wh"]
        self._set_values(value_dict)

