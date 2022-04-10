import datetime
import logging
from config.config import Config
from utils.sun_angles import SunAngles

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
_LOGGER = logging.getLogger(__name__)


def main():
    sun_angles = SunAngles(Config.LONGITUDE, Config.LATITUDE)

    now = datetime.datetime.now()
    for hour in range(0, 23):
        date_time = now.replace(hour=hour, minute=2)
        _LOGGER.info("Hour: %s \t Min %s \t %s" % (hour, date_time.minute, sun_angles.is_daytime(date_time)))


if __name__ == "__main__":
    main()
