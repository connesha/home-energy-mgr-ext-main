import logging
from actions.action_forecast import ForecastAction
from actions.action_plot import PlotAction
from harnesses.harness_common_utility import ExampleUtility


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)


def main():
    services = ExampleUtility.create_refreshed_services(['SolarConfig', 'DbForecastDaily', 'DbRadiationHourly'])

    plot_action = PlotAction(to_file=True, show=False, output_folder="/Users/shane.conneely/PycharmProjects")
    # plot_action.add_pre_action(UpdateGenerationAction(UpdateGenerationAction.DAY_TODAY))
    plot_action.add_pre_action(ForecastAction(ForecastAction.TOMORROW, single_day=False))

    plot_action.execute(services)

    ExampleUtility.close_services(services)


if __name__ == "__main__":
    main()
