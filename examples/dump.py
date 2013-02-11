#!/usr/bin/env python
"""
This is an example script to dump all available fitbit data.
This can be set up in a cronjob to dump data daily.

Run with the following parameters:
$ python dump.py <email> <password> <directory>
"""
import datetime
import os
import sys
import time

import fitbit

EMAIL=sys.argv[1]
PASSWORD=sys.argv[2]
DUMP_DIR=sys.argv[3]

def dump_to_str(data):
    return "\n".join(["%s,%s" % (str(ts), v) for ts, v in data])

def dump_to_file(data_type, date, data):
    directory = "%s/%i/%s" % (DUMP_DIR, date.year, date)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    with open("%s/%s.csv" % (directory, data_type), "w") as f:
        f.write(dump_to_str(data))
    time.sleep(1)

def previously_dumped(date):
    return os.path.isdir("%s/%i/%s" % (DUMP_DIR, date.year, date))

def dump_day(c, date):
    steps = c.intraday_steps(date)
    # Assume that if no steps were recorded then there is no data
    if sum([s[1] for s in steps]) == 0:
        return False

    dump_to_file("steps", date, steps)
    dump_to_file("calories", date, c.intraday_calories_burned(date))
    dump_to_file("active_score", date, c.intraday_active_score(date))
    dump_to_file("sleep", date, c.intraday_sleep(date))

    return True

if __name__ == '__main__':
    #import logging
    #logging.basicConfig(level=logging.DEBUG)
    client = fitbit.Client.login(EMAIL, PASSWORD)

    date = datetime.date.today()

    # Look for the most recent sync
    while (datetime.date.today() - date).days < 365:
        r = dump_day(client, date)
        date -= datetime.timedelta(days=1)
        if r:
            break

    if (datetime.date.today() - date).days > 365:
        # No sync in the last year.
        sys.exit(1)

    while not previously_dumped(date):
        r = dump_day(client, date)
        date -= datetime.timedelta(days=1)
        if not r:
            break

    # Always redump the last dumped day because we may have dumped it before the day was finished.
    dump_day(client, date)
