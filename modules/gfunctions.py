from datetime import datetime

VERSION = "1.2"

class Runned:
    _RUNNED = False

    @property
    @staticmethod
    def runned():
        return Runned._RUNNED

    @runned.setter
    @staticmethod
    def runned(val):
        if isinstance(val, bool):
            Runned._RUNNED = val
        else:
            raise Exception('Runned: runned val is not bool')

def map_func(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def array_ma(array):
    try:
        summ = 0
        for el in array:
            summ += el
        return summ / len(array)
    except:
        return 0


def clear_str(str_):
    str_ = str(str_)
    str_ = str_.replace("\\r\\n", '')
    str_ = str_.replace("b'", '')
    str_ = str_.replace("'", '')
    return str_


def difference_between_date(date1, date2, format=None):
    duration = date2 - date1
    duration_in_s = duration.total_seconds()  # Total number of seconds between dates
    days = divmod(duration_in_s, 86400)  # Get days (without [0]!)
    hours = divmod(days[1], 3600)  # Use remainder of days to calc hours
    minutes = divmod(hours[1], 60)  # Use remainder of hours to calc minutes
    seconds = divmod(minutes[1], 1)  # Use remainder of minutes to calc seconds
    return "%d дней, %d часов, %d минут и %d секунд" % (days[0], hours[0], minutes[0], seconds[0])

def find_in_list(lst, value):
    for el in lst:
        if el == value:
            return True
    return False

class JList(list):
    def find(self, value):
        for el in self:
            if el == value:
                return True
        return False

    def delete(self, value):
        try:
            self.remove(value)
            return True
        except ValueError:
            return False

class GFunctions:
    @staticmethod
    def clear_str(str):
        return clear_str(str)

    @staticmethod
    def difference_between_date(date1, date2):
        return difference_between_date(date1, date2)

    @staticmethod
    def find_in_list(*args):
        return find_in_list(*args)

class JPrint:
    __NAME = 'Jarvis'

    @staticmethod
    def jprint(s):
        __now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        print(__now+" "+JPrint.__NAME+": "+str(s))
