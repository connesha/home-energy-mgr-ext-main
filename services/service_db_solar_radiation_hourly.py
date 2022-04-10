import logging
from mysql.connector import Error

from services.db_base import DbBase
from services.service_base import ServiceBase

DATE_STR_FORMAT = '%Y-%m-%d'
_DB_TABLE = "solar_radiation_hourly"

_LOGGER = logging.getLogger(__name__)


class DbRadiationHourly(DbBase, ServiceBase):

    def __init__(self, host, database, user, password):
        DbBase.__init__(self, host, database, user, password)
        ServiceBase.__init__(self)
        self._table = _DB_TABLE
        return

    def refresh(self):
        super().refresh()
        self.close()    # TODO: would prefer not to close each time, but the queries are being cached. Need to look into it, closing for now
        self._connect_if_necessary()
        return

    def close(self):
        DbBase.close(self)
        ServiceBase.close(self)
        return

    def get_actual_factors(self, date_from, date_to):
        cur = self._connection.cursor()
        try:
            sql_statement = "SELECT radiation, actual_wh from %s " \
                            "WHERE date >= '%s' and date <= '%s' AND actual_wh IS NOT NULL" % \
                            (self._table, date_from, date_to)

            cur.execute(sql_statement)
            results_tuple = cur.fetchall()
            # _LOGGER.debug(results_tuple)
            result_list = []
            for radiation, actual_wh in results_tuple:
                if actual_wh and radiation:
                    factor = actual_wh / radiation
                    result_list.append(factor)

            return result_list

        except Error:
            _LOGGER.exception("Error executing")
            exit(1)
        finally:
            cur.close()

    def insert_or_update_radiations(self, date, radiation_list):
        cur = self._connection.cursor()
        try:
            date_str = date.strftime(DATE_STR_FORMAT)
            sql_statement = "INSERT INTO %s (date" % self._table
            for i in range(0, 24):
                sql_statement += ", `%s:00`" % radiation_list[i][0]
            sql_statement += ") VALUES ('%s'" % date_str
            for i in range(0, 24):
                sql_statement += ", '%s'" % radiation_list[i][1]
            sql_statement += ") "
            sql_statement += "ON DUPLICATE KEY UPDATE "
            for i in range(0, 24):
                sql_statement += "`%s:00` = '%s'" % (radiation_list[i][0], radiation_list[i][1])
                if i != 23:
                    sql_statement += ", "

            # _LOGGER.debug(sql_statement)
            cur.execute(sql_statement)

        except Error:
            _LOGGER.exception("Error executing")
            exit(1)
        finally:
            cur.close()

    def get_hourly_forecast(self, start_date):
        cur = self._connection.cursor()
        try:
            date_str = start_date.strftime(DATE_STR_FORMAT)
            sql_statement = "SELECT * " \
                            "FROM %s " \
                            "WHERE date >= '%s'" % \
                            (self._table, date_str)

            cur.execute(sql_statement)
            results_tuple = cur.fetchall()
            return results_tuple

        except Error:
            _LOGGER.exception("Error executing")
            exit(1)
        finally:
            cur.close()

    def delete_date(self, date):
        cur = self._connection.cursor()
        try:
            date_str = date.strftime(DATE_STR_FORMAT)
            sql_statement = "DELETE from %s " \
                            "WHERE date = '%s'" % \
                            (self._table, date_str)
            cur.execute(sql_statement)
        except Error:
            _LOGGER.exception("Error executing")
        finally:
            cur.close()

