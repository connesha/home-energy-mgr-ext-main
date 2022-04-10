import datetime


class Utils:

    def __init__(self):
        return

    @staticmethod
    def date_from_offset(offset=0):
        return datetime.date.today() + datetime.timedelta(days=offset)

    @staticmethod
    def date_from_date_offset(date, offset=0):
        return date + datetime.timedelta(days=offset)

    @staticmethod
    def date_today():
        return datetime.date.today()

    @staticmethod
    def date_tomorrow():
        return Utils.date_from_offset(1)

    @staticmethod
    def date_yesterday():
        return Utils.date_from_offset(-1)

    @staticmethod
    def time_now():
        return datetime.datetime.now()

    @staticmethod
    def time_diff_mins(start_time, end_time):
        duration = end_time - start_time
        duration_mins = int(round(duration.total_seconds() / 60))
        return duration_mins

    @staticmethod
    def clamp_value(value, min_value, max_value):
        if value > max_value:
            return max_value
        elif value < min_value:
            return min_value
        else:
            return value

    @staticmethod
    def time_in_range(start, end, x):
        """Return true if x is in the range [start, end]"""
        if start <= end:
            return start <= x <= end
        else:
            return start <= x or x <= end
