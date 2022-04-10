import json
import logging
from mysql.connector import Error

from services.db_base import DbBase

_LOGGER = logging.getLogger(__name__)


class ObjectView(object):
    def __init__(self, d):
        self.__dict__ = d


class DbProperties(DbBase):

    def __init__(self, host, database, table, user, password):
        super().__init__(host, database, user, password)
        self._table = table
        self.values = None
        return

    def reload(self):
        _LOGGER.debug("reload")
        self.close()        # TODO: would prefer not to close each time, but the queries are being cached. Need to look into it, closing for now
        self._connect_if_necessary()
        value_dict = self._read_properties()
        self._set_values(value_dict)

    def _read_properties(self):
        cur = self._connection.cursor()

        try:
            sql_statement = "SELECT * FROM %s" % self._table
            _LOGGER.debug("sql_statement: %s" % sql_statement)
            cur.execute(sql_statement)

            value_dict = {}
            for row in cur:
                prop_key = row[0]
                prop_value = row[1]
                prop_type = row[2]
                if prop_type == "int":
                    dict_val = int(prop_value)
                elif prop_type == "float":
                    dict_val = float(prop_value)
                elif prop_type == "list":
                    dict_val = json.loads(prop_value)
                else:
                    dict_val = prop_value.lower()
                value_dict[prop_key] = dict_val

            return value_dict

        except Error:
            _LOGGER.exception("Error executing")
            exit(1)
        finally:
            cur.close()

    def _set_values(self, value_dict):
        self.values = ObjectView(value_dict)

