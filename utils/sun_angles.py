import logging
import pytz
from utils.utils import Utils
from astropy.coordinates import get_sun, AltAz, EarthLocation
from astropy.time import Time
from suntime import Sun

_LOGGER = logging.getLogger(__name__)


class SunAngles:

    def __init__(self, longitude, latitude):
        self.longitude = longitude
        self.latitude = latitude
        return

    # noinspection PyBroadException
    def get_bounded_num_days_back_within_angle(self, angle, lower_limit, upper_limit):
        num_days = 0
        try:
            location = EarthLocation.from_geodetic(self.longitude, self.latitude)
            sun = Sun(self.latitude, self.longitude)

            solar_noon_time_today = self.get_solar_noon_for_date(sun, Utils.date_today())
            zen_angle_today = self.zen_angle_at_date(solar_noon_time_today, location)

            angle_sum = 0
            last_angle = zen_angle_today
            while num_days <= upper_limit:
                date = Utils.date_from_offset(-(num_days + 1))
                solar_noon_time = self.get_solar_noon_for_date(sun, date)
                zen_angle = self.zen_angle_at_date(solar_noon_time, location)
                diff_from_last = abs(last_angle - zen_angle)
                if angle_sum + diff_from_last > angle:
                    break
                angle_sum += abs(last_angle - zen_angle)
                last_angle = zen_angle
                num_days += 1

        except Exception:
            _LOGGER.exception("SunAngles could not get num days")

        num_days = Utils.clamp_value(num_days, lower_limit, upper_limit)
        return num_days

    def get_solar_noon_for_date(self, sun, date):
        tz_ireland = pytz.timezone('Europe/Dublin')
        sunrise_time = sun.get_sunrise_time(date)
        sunset_time = sun.get_sunset_time(date)
        sunrise_time_local_tz = sunrise_time.astimezone(tz_ireland)
        sunset_time_local_tz = sunset_time.astimezone(tz_ireland)

        # midpoint is technically not 100% accurate for SolarNoon, but it's very close, and plenty good enough for this purpose
        solar_noon = sunrise_time_local_tz + (sunset_time_local_tz - sunrise_time_local_tz) / 2

        return solar_noon

    def zen_angle_at_date(self, date_time, location):
        altaz = AltAz(obstime=date_time, location=location)
        astropy_time = Time(date_time)
        zen_ang = get_sun(astropy_time).transform_to(altaz).zen
        degrees = zen_ang.degree
        return degrees

    def get_sunrise_for_date(self, date):
        sun = Sun(self.latitude, self.longitude)
        tz_ireland = pytz.timezone('Europe/Dublin')
        sunrise_time = sun.get_sunrise_time(date)
        sunrise_time_local_tz = sunrise_time.astimezone(tz_ireland)
        return sunrise_time_local_tz

    def get_sunset_for_date(self, date):
        sun = Sun(self.latitude, self.longitude)
        tz_ireland = pytz.timezone('Europe/Dublin')
        sunset_time = sun.get_sunset_time(date)
        sunset_time_local_tz = sunset_time.astimezone(tz_ireland)
        return sunset_time_local_tz

    def is_daytime(self, date_time):
        sun = Sun(self.latitude, self.longitude)
        tz_ireland = pytz.timezone('Europe/Dublin')
        sunrise_time = sun.get_sunrise_time(date_time)
        sunset_time = sun.get_sunset_time(date_time)
        sunrise_time_local_tz = sunrise_time.astimezone(tz_ireland)
        sunset_time_local_tz = sunset_time.astimezone(tz_ireland)
        compare_time = date_time.astimezone(tz_ireland)
        # _LOGGER.debug(sunrise_time_local_tz)
        # _LOGGER.debug(sunset_time_local_tz)
        if sunrise_time_local_tz < compare_time < sunset_time_local_tz:
            return True
        else:
            return False
