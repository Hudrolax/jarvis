import datetime

def value_filled(val):
    if isinstance(val, datetime.datetime):
        return val != datetime.datetime(1, 1, 1, 0, 0, 0)
    elif isinstance(val, str):
        return val != ""
    elif isinstance(val, int) or isinstance(val, float):
        return val != 0
    else:
        False