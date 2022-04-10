import logging
from mysql.connector import Error

from config.config import Config
from services.db_base import DbBase
from services.service_base import ServiceBase
from utils.utils import Utils

DATE_STR_FORMAT = '%Y-%m-%d'
_DB_TABLE = "solar_forecasts"

_LOGGER = logging.getLogger(__name__)


class DbForecastDaily(DbBase, ServiceBase):

    def __init__(self, host, database, user, password):
        DbBase.__init__(self, host, database, user, password)
        ServiceBase.__init__(self)
        self._table = _DB_TABLE
        return

    def refresh(self):
        super().refresh()
        self.close()   # TODO: would prefer not to close each time, but the queries are being cached. Need to look into it, closing for now
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
            _LOGGER.debug("sql_statement: %s" % sql_statement)
            cur.execute(sql_statement)
            results_tuple = cur.fetchall()
            _LOGGER.debug(results_tuple)
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

    def get_forecast_wh(self, date):
        cur = self._connection.cursor()
        forecast_wh = None

        try:
            sql_statement = "SELECT forecast_wh FROM %s " \
                            "WHERE date = '%s'" % \
                            (self._table, date)
            _LOGGER.debug("sql_statement: %s" % sql_statement)
            cur.execute(sql_statement)
            for row in cur:
                forecast_wh = row[0]

            return forecast_wh

        except Error:
            _LOGGER.exception("Error executing")
            exit(1)
        finally:
            cur.close()

    def is_charge_set_for_date(self, date):
        cur = self._connection.cursor()
        try:
            sql_statement = "SELECT charge_on FROM %s " \
                            "WHERE date = '%s'" % \
                            (self._table, date)
            _LOGGER.debug("sql_statement: %s" % sql_statement)
            cur.execute(sql_statement)
            for row in cur:
                charge_on = row[0]
                if charge_on == 0 or charge_on == 1:
                    return True

            return False

        except Error:
            _LOGGER.exception("Error executing")
            exit(1)
        finally:
            cur.close()

    def get_actual_factors_similar_radiation(self, date_from, date_to, radiation, limit):
        # TODO: move this to a different layer
        cur = self._connection.cursor()
        try:
            sql_statement = "SELECT radiation, actual_wh from %s " \
                            "WHERE date >= '%s' and date <= '%s' AND actual_wh IS NOT NULL " \
                            "ORDER BY radiation asc" % \
                            (self._table, date_from, date_to)
            _LOGGER.debug("sql_statement: %s" % sql_statement)
            cur.execute(sql_statement)
            results_tuple = cur.fetchall()

            filtered_list = self._filter_similar_radiaions(results_tuple, radiation, limit)

            result_list = []
            for radiation, actual_wh in filtered_list:
                if actual_wh and radiation:
                    factor = actual_wh / radiation
                    result_list.append(factor)

            return result_list

        except Error:
            _LOGGER.exception("Error executing")
            exit(1)
        finally:
            cur.close()

    def get_actual_factor_sum_similar_radiation(self, last_date, num_days_back, radiation, limit):
        # TODO: move this to a different layer
        cur = self._connection.cursor()
        date_from = Utils.date_from_date_offset(last_date, -num_days_back)
        try:
            sql_statement = "SELECT radiation, actual_wh, date from %s " \
                            "WHERE date > '%s' and date <= '%s' AND actual_wh IS NOT NULL " \
                            "ORDER BY radiation asc" % \
                            (self._table, date_from, last_date)
            _LOGGER.debug("sql_statement: %s" % sql_statement)
            cur.execute(sql_statement)
            results_tuple = cur.fetchall()

            filtered_list = self._filter_similar_radiaions(results_tuple, radiation, limit)

            radiation_total = 0
            actual_wh_total = 0
            for radiation, actual_wh in filtered_list:
                radiation_total += radiation
                actual_wh_total += actual_wh

            if radiation_total == 0:
                return Config.FORECAST_FACTOR_INITIAL
            return actual_wh_total / radiation_total

        except Error:
            _LOGGER.exception("Error executing")
            exit(1)
        finally:
            cur.close()

    def _filter_similar_radiaions(self, results_tuple, radiation, limit):
        # TODO: not the most elegant... but it works....
        # TODO: move to different layer
        # get the list of ones to exclude
        exclude_list = []
        top_index = len(results_tuple) - 1
        bottom_index = 0
        while (len(results_tuple) - len(exclude_list)) > limit:
            bottom_radiation = results_tuple[bottom_index][0]
            top_radiation = results_tuple[top_index][0]
            if radiation - bottom_radiation < top_radiation - radiation:
                exclude_list.append(top_index)
                top_index -= 1
            else:
                exclude_list.append(bottom_index)
                bottom_index += 1

        # make a new list from the ones not in exclude_list
        result_list = []
        index = 0
        while len(result_list) < limit and index < len(results_tuple):
            if index not in exclude_list:
                result_list.append([results_tuple[index][0], results_tuple[index][1]])
            index += 1

        return result_list

    def get_forecast_vs_actuals(self, start_date):
        cur = self._connection.cursor()
        try:
            date_str = start_date.strftime(DATE_STR_FORMAT)
            sql_statement = "SELECT date, forecast_wh, actual_wh, radiation " \
                            "FROM %s " \
                            "WHERE date >= '%s'" % \
                            (self._table, date_str)
            _LOGGER.debug("sql_statement: %s" % sql_statement)
            cur.execute(sql_statement)
            results_tuple = cur.fetchall()
            return results_tuple

        except Error:
            _LOGGER.exception("Error executing")
            exit(1)
        finally:
            cur.close()

    def insert_forecast(self, date, radiation, forecast_factor, forecast_wh):
        cur = self._connection.cursor()
        try:
            date_str = date.strftime(DATE_STR_FORMAT)
            sql_statement = "INSERT INTO %s " \
                            "(date, radiation, forecast_factor, forecast_wh) " \
                            "VALUES ('%s', %s, %s, %s)" % \
                            (self._table, date_str, radiation, forecast_factor, forecast_wh)
            _LOGGER.debug("sql_statement: %s" % sql_statement)
            cur.execute(sql_statement)
        except Error:
            _LOGGER.exception("Error executing")
            exit(1)
        finally:
            cur.close()

    def insert_or_update_forecast(self, date, radiation, forecast_factor, forecast_wh):
        cur = self._connection.cursor()
        try:
            date_str = date.strftime(DATE_STR_FORMAT)
            sql_statement = "INSERT INTO %s " \
                            "(date, radiation, forecast_factor, forecast_wh) " \
                            "VALUES ('%s', %s, %s, %s) " \
                            "ON DUPLICATE KEY " \
                            "UPDATE " \
                            "radiation=%s, forecast_factor=%s, forecast_wh=%s" % \
                            (self._table, date_str, radiation, forecast_factor, forecast_wh, radiation, forecast_factor, forecast_wh)
            _LOGGER.debug("sql_statement: %s" % sql_statement)
            cur.execute(sql_statement)

        except Error:
            _LOGGER.exception("Error executing")
            exit(1)
        finally:
            cur.close()

    def update_actual_wh(self, date, actual_wh):
        cur = self._connection.cursor()
        try:
            date_str = date.strftime(DATE_STR_FORMAT)
            sql_statement = "UPDATE %s " \
                            "SET actual_wh = %s " \
                            "WHERE date = '%s'" % \
                            (self._table, actual_wh, date_str)
            _LOGGER.debug("sql_statement: %s" % sql_statement)
            cur.execute(sql_statement)
        except Error:
            _LOGGER.exception("Error executing")
            exit(1)
        finally:
            cur.close()

    def update_charge(self, date, battery_initial_wh, charge_on, charge_wh=0, charge_da=0):
        cur = self._connection.cursor()
        try:
            date_str = date.strftime(DATE_STR_FORMAT)
            if charge_on:
                sql_statement = "UPDATE %s " \
                                "SET battery_initial_wh = %s, charge_on = %s, charge_wh = %s, charge_da = %s " \
                                "WHERE date = '%s'" % \
                                (self._table, battery_initial_wh, charge_on, charge_wh, charge_da, date_str)
            else:
                sql_statement = "UPDATE %s " \
                                "SET battery_initial_wh = %s, charge_on = %s " \
                                "WHERE date = '%s'" % \
                                (self._table, battery_initial_wh, charge_on, date_str)
            _LOGGER.debug("sql_statement: %s" % sql_statement)
            cur.execute(sql_statement)
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
            _LOGGER.debug("sql_statement: %s" % sql_statement)
            cur.execute(sql_statement)
        except Error:
            _LOGGER.exception("Error executing")
        finally:
            cur.close()
