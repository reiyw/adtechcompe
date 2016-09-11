import datetime
import badgets as bg
import json


def time_remain_percent():
    now_datetime = datetime.datetime.now()
    now = now_datetime.hour * 60 + now_datetime.minute

    start_date = now_datetime.replace(hour=1, minute=00) #TODO:start time
    start = start_date.hour * 60 + start_date.minute

    end_date = now_datetime.replace(hour=23, minute=00) #TODO:end time
    end = end_date.hour * 60 + end_date.minute

    time_remain_percent = float((now - end)) / (start - end)

    return time_remain_percent

def debug_budget():
    for k, v in bg.get_budgets().items():
        print k
        print v
    return bg.get_budgets()
