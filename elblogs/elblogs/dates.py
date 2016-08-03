# Utils for munging dates and date strings

from datetime import datetime, date, timedelta, time


EPOCH = datetime.utcfromtimestamp(0)
DAY_IN_S = 60*60*24


def start_and_end(before_date=None, days=1):
    ''' Given a date, generate a range of start, end for the number of days prior'''
    if before_date:
        before_date = datetime.strptime(before_date, "%Y%m%d").date()
    else:
        before_date = date.today()

    start_date = before_date - timedelta(days=days)
    end_date = before_date - timedelta(days=1)
    return start_date, end_date

def date_range_label(start, end):
    ''' Pretty format a label for the range of dates'''
    daterange = start.strftime("%B %d")
    if start != end:
        daterange += " to " + end.strftime("%B %d")
    return daterange

def date_to_dogtime(start, end):
    ''' Take datetime.dates and return inclusive unix-epoch second ranges'''
    return unix_time_s(start), unix_time_s(end) + DAY_IN_S - 1

def unix_time_s(dt):
    ''' Convert datetime to integer seconds. Thanks StackOverflow.'''
    if (isinstance(dt, date)):
        ## Make it datetime
        dt = datetime.combine(dt, time())
    return (dt - EPOCH).total_seconds()
