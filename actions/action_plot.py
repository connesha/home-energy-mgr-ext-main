import datetime
import logging
from config.config import Config
from matplotlib import pyplot as plt
from actions.action_base import ActionBase
from utils.sun_angles import SunAngles
from utils.utils import Utils

_LOGGER = logging.getLogger(__name__)

logging.getLogger('matplotlib.font_manager').disabled = True

_COLOR_LIST = ['forestgreen', 'firebrick', 'mediumblue', 'darkorange', 'darkviolet', 'darkgoldenrod', 'hotpink',
               'yellow', 'lightslategray']

_FILE_NAME_DAILY = "plot_latest_daily.png"
_FILE_NAME_HOURLY = "plot_latest_hourly.png"


class PlotAction(ActionBase):

    def __init__(self, to_file=False, show=True, output_folder=None):
        super().__init__()
        self.to_file = to_file
        self.show = show
        if output_folder is not None:
            self.file_path_daily = output_folder + "/" + _FILE_NAME_DAILY
            self.file_path_hourly = output_folder + "/" + _FILE_NAME_HOURLY
        else:
            self.file_path_daily = _FILE_NAME_DAILY
            self.file_path_hourly = _FILE_NAME_HOURLY

    def can_execute_now(self, services):
        super().can_execute_now(services)
        return self.is_in_last_run_limit_secs(services.get_service("SolarConfig").values.action_freq_secs_plot)

    def execute_impl(self, services):
        super().execute_impl(services)
        _LOGGER.info("execute_impl")

        # get the services that are needed
        solar_config = services.get_service("SolarConfig")
        db_forecast_daily = services.get_service("DbForecastDaily")
        db_rad_hourly = services.get_service("DbRadiationHourly")

        self._plot_daily(db_forecast_daily, solar_config)
        self._plot_hourly(db_rad_hourly)

        _LOGGER.info("execute_impl done")

    # noinspection PyTypeChecker
    def _plot_hourly(self, db_rad_hourly):
        # get data from db
        results_tuple = db_rad_hourly.get_hourly_forecast(Utils.date_yesterday())

        # put the data into individual lists, ready for setting on the graph
        dates_list, forecast_list = self.extract_hourly_lists_from_tuple(results_tuple)
        times_list = []
        for i in range(0, 24):
            times_list.append("%s:00" % i)

        # trim the lists, so not crowding UI with nighttime hours
        morning_trim_count = 5
        evening_trim_count = 1
        self.trim_list(times_list, morning_trim_count, evening_trim_count)
        for the_list in forecast_list:
            self.trim_list(the_list, morning_trim_count, evening_trim_count)

        # setup the axes and plot
        date_yesterday = Utils.date_yesterday()
        date_today = Utils.date_today()
        date_tomorrow = Utils.date_tomorrow()
        fig, axis = plt.subplots(1, 1)
        axis.set_xticks(range(0, len(times_list)))
        axis.set_xticklabels(times_list, rotation=60, fontsize=11, ha="right")
        for i in range(0, len(dates_list)):
            the_list = forecast_list[i]
            date = dates_list[i]
            if date == date_yesterday:
                dates_list[i] = "yesterday"
                linewidth = 1
            elif date == date_today:
                linewidth = 4
                dates_list[i] = "today"
            elif date == date_tomorrow:
                linewidth = 3
                dates_list[i] = "tomorrow"
            else:
                linewidth = 1
            axis.plot(the_list, linestyle='-', linewidth=linewidth, marker='o', color=_COLOR_LIST[i],
                      label="%s" % dates_list[i])

        # labels, legends, format, etc
        axis.legend()
        axis.grid()
        axis.set_ylabel("radiation", fontsize=18)
        title = "Hourly Radiation (%s)" % date_today
        plt.title(title)
        # make it all fit
        plt.subplots_adjust(bottom=0.25)
        fig.set_tight_layout(True)
        # save to file
        if self.to_file:
            plt.savefig(self.file_path_hourly)
        # show
        if self.show:
            plt.show()
        else:
            plt.close('all')

    @staticmethod
    def trim_list(the_list, start_trim_count, end_trim_count):
        # trim start
        for i in range(0, start_trim_count):
            the_list.pop(0)
        # trim end
        for i in range(0, end_trim_count):
            the_list.pop(len(the_list) - 1)

    def _plot_daily(self, db_forecast_daily, solar_config):
        # how far to go back. go back as far as out forecast window, if no override set
        sun_angles = SunAngles(Config.LONGITUDE, Config.LATITUDE)
        num_days_history = sun_angles.get_bounded_num_days_back_within_angle(solar_config.values.forecast_sun_angle_max,
                                                                             solar_config.values.forecast_num_days_history_min,
                                                                             solar_config.values.forecast_num_days_history_max)
        if solar_config.values.plot_num_days_past_override > 0:
            num_days_history_to_plot = solar_config.values.plot_num_days_past_override
        else:
            num_days_history_to_plot = num_days_history
        # get data from db
        results_tuple = db_forecast_daily.get_forecast_vs_actuals(Utils.date_from_offset(-num_days_history_to_plot))
        # put the data into individual lists, ready for setting on the graph
        actuals_list, dates_list, forecasts_list, radiation_list = self.extract_lists_from_tuple(results_tuple)
        # setup the axes
        fig, ax_kwh = plt.subplots(1, 1)
        ax_rad = ax_kwh.twinx()
        # kwh x axis
        ax_kwh.set_xticks(range(0, len(dates_list)))
        ax_kwh.set_xticklabels(dates_list, rotation=60, fontsize=9, ha="right")
        # kwh plot
        ax_kwh.plot(forecasts_list, linestyle='-', linewidth=2, marker='o', color='firebrick', label='forecast kwh')
        ax_kwh.plot(actuals_list, linestyle='-', linewidth=2, marker='o', color='mediumblue', label='actual kwh')
        # rad plot
        ax_rad.bar(range(len(radiation_list)), radiation_list, color='dimgray', width=len(radiation_list) / 150,
                   label='radiation')
        # grid
        ax_kwh.grid()
        # y axis
        ax_kwh.set_ylabel("kwh", fontsize=18)
        ax_rad.set_ylabel("radiation", fontsize=18)
        # legend
        lines1, labels1 = ax_kwh.get_legend_handles_labels()
        lines2, labels2 = ax_rad.get_legend_handles_labels()
        ax_rad.legend(lines1 + lines2, labels1 + labels2, loc='lower left', fontsize=11)
        # title
        title = "Daily Forecast vs Actual Generation %sd (%s)" % (
            num_days_history, (datetime.datetime.now()).strftime('%H:%M'))
        plt.title(title)
        # make it all fit
        plt.subplots_adjust(bottom=0.25)
        ax_kwh.set_ylim(ymin=0)
        if len(actuals_list) > 0:  # covering the case where this is run for the first time and actuals_list is empty
            max_actuals_list = max(actuals_list)
        else:
            max_actuals_list = 0
        y_limit = (max(max(forecasts_list), max_actuals_list) + 5)
        ax_kwh.set_ylim(ymax=y_limit)
        fig.set_tight_layout(True)
        # save to file
        if self.to_file:
            plt.savefig(self.file_path_daily)
        # show
        if self.show:
            plt.show()
        else:
            plt.close('all')

    def extract_lists_from_tuple(self, results_tuple):
        dates_list = []
        forecasts_list = []
        actuals_list = []
        radiation_list = []
        for date, forecast, actual, radiation in results_tuple:
            dates_list.append(date.strftime('%d-%m-%Y'))
            forecasts_list.append(forecast / 1000)
            if actual:
                actuals_list.append(actual / 1000)
            radiation_list.append(radiation)
        return actuals_list, dates_list, forecasts_list, radiation_list

    def extract_hourly_lists_from_tuple(self, results_tuple):
        dates_list = []
        forecast_list = []

        for day in results_tuple:
            # _LOGGER.debug(day)
            forecast_day_list = []
            for col in day:
                if isinstance(col, datetime.date):
                    dates_list.append(col)
                else:
                    forecast_day_list.append(col)
            forecast_list.append(forecast_day_list)

        return dates_list, forecast_list
