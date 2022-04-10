import logging
import urllib.request
import xml.etree.ElementTree as ElementTree
from pandas import DataFrame, to_datetime
import datetime
from config.config import Config

WEATHER_URL = "http://metwdb-openaccess.ichec.ie/metno-wdb2ts/locationforecast?lat=%s;long=%s" % \
              (Config.LATITUDE, Config.LONGITUDE)

_LOGGER = logging.getLogger(__name__)


class WeatherForecast:

    def __init__(self):
        self.weather_data_frame = None
        return

    def get_radiation_for_date_total(self, date):
        daily_weather_data = self.weather_data_frame.resample('H').ffill().resample('D').sum().iterrows()
        radiation = self._extract_radiation_for_date_total(daily_weather_data, date)
        return int(round(radiation))

    def get_radiation_for_today_total(self):
        return self.get_radiation_for_date_total(datetime.date.today())

    def get_radiation_for_date_hourly(self, date):
        hourly_weather_data = self.weather_data_frame.resample('H').ffill().iterrows()
        radiation_list = self._extact_hourly_radiation_for_date(hourly_weather_data, date)
        self._ensure_full_day(radiation_list)
        return radiation_list

    def get_radiation_for_today_hourly(self):
        return self.get_radiation_for_date_hourly(datetime.date.today())

    def load_weather_data(self):
        response = urllib.request.urlopen(WEATHER_URL)
        data = response.read()
        tree = ElementTree.fromstring(data)
        parent_map = {c: p for p in tree.iter() for c in p}
        result_dict = {}
        for n in tree.iter('globalRadiation'):
            result_dict[parent_map[parent_map[n]].attrib['from']] = n.attrib['value']
        self.weather_data_frame = DataFrame.from_dict(result_dict, orient='index')
        self.weather_data_frame.index = self.weather_data_frame.index.map(to_datetime)
        self.weather_data_frame.columns = ['globalRadiation']
        self.weather_data_frame['globalRadiation'] = self.weather_data_frame.globalRadiation.astype('float')
        # _LOGGER.debug(self.weather_data_frame.resample('H').ffill().resample('D').sum())
        # _LOGGER.debug(self.weather_data_frame[self.weather_data_frame['globalRadiation'] != 0][:12])
        return

    @staticmethod
    def _ensure_full_day(radiation_list):
        # when you get data for TODAY, it will only be from this hoiur onweards, so pad the previous hours
        first_hour = radiation_list[0][0]
        # _LOGGER.debug(radiation_list)
        if first_hour != 0:
            for i in range(first_hour, 0, -1):
                radiation_list.insert(0, [i-1, 0])
        # _LOGGER.debug(radiation_list)

    @staticmethod
    def _extact_hourly_radiation_for_date(hourly_weather_data, date_to_get):
        hourly_radiation = []
        for index, row in hourly_weather_data:
            radiation = int(round(row['globalRadiation']))
            radiation_date = index.to_pydatetime().date()
            radiation_hour = index.to_pydatetime().time().hour
            if radiation_date == date_to_get:
                hourly_radiation.append([radiation_hour, radiation])

        return hourly_radiation

    @staticmethod
    def _extract_radiation_for_date_total(daily_weather_data, date_to_get):
        for index, row in daily_weather_data:
            radiation = row['globalRadiation']
            radiation_date = index.to_pydatetime().date()
            if radiation_date == date_to_get:
                return radiation
