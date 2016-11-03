#!/usr/bin/env python
"""
This is an example script to dump all available fitbit data.
This can be set up in a cronjob to dump data daily.

You can add your passwords to a file ~/.fitbit in the form below and then you don't need to include it on the command line.

email1:[password1]
email2:[password2]

Run with the following parameters:
$ python dump.py <email> <password - optional> <directory>
"""
import datetime
import os
import sys
import time
import getpass
from optparse import OptionParser

sys.path.append(os.getcwd())

import fitbit
parser = OptionParser()
account_file="~/.fitbit"
parser.add_option("-e", "--email", dest="email", help="Account email. Default to "+account_file+" account if only one is set.")
parser.add_option("-p", "--pwd", dest="password", help="Account password. Can be saved in "+account_file+" as email:[pwd]")
parser.add_option("-d", "--dir", dest="dir", help="Path to save your data.", default="data")
parser.add_option("-c", "--continue",action="store_true", dest="continue_dumping_old", help="Continue sync even before last previously downloaded data.")
parser.add_option("-f", "--force",action="store_true", dest="force", help="Force re-downloading of each days.")
parser.add_option("-s", "--start-date", dest="start_date", help="Minimal date to check. Default is 2010-01-01 .", default="2010-01-01")
parser.add_option("-m", "--max-empty-days", dest="nEmptyDayMax",default=10, help="Number of no-data days after which we stop. Default is 10.")
(options, args) = parser.parse_args()

ACCOUNTS_FILE=os.path.expanduser(account_file)
if not options.email or not options.password:
    if os.path.isfile(ACCOUNTS_FILE):
        fp = open(ACCOUNTS_FILE, "r")
        accounts=[line.split(":") for line in fp.readlines()]
    else:
        accounts=[]

if not options.email:
    if len(accounts)==1: 
        options.email = accounts[0][0].strip()
    else:
        print "No account set. Please read the help by running:\n      ",sys.argv[0]," --help"
        exit(0)

print "Downloading data for account : ", options.email
if not options.password:
    options.password = [account[1] for account in accounts if account[0] == options.email][0].strip()
    if options.password:
        print "  Using password from config file"
    else:
        password = getpass.getpass("Enter your password:")

print "  Saving in : ", options.dir
def dump_to_str(data):
    return "\n".join(["%s,%s" % (str(ts), v) for ts, v in data])

def dump_to_file(data_type, date, data):
    directory = "%s/%i/%s" % (options.dir, date.year, date)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    with open("%s/%s.csv" % (directory, data_type), "w") as f:
        f.write(dump_to_str(data))
    time.sleep(1)

def previously_dumped(date):
    return os.path.isdir("%s/%i/%s" % (options.dir, date.year, date))

def dump_day(c, date):
    steps = c.intraday_steps(date)
    # Assume that if no steps were recorded then there is no data
    if sum([s[1] for s in steps]) == 0:
        return False

    dump_to_file("steps", date, steps)
    #dump_to_file("calories", date, c.intraday_calories_burned(date))
    #dump_to_file("floor", date, c.intraday_floor_climbed(date))
    #dump_to_file("active_score", date, c.intraday_active_score(date))
    dump_to_file("sleep", date, c.intraday_sleep(date))
    detailed=["CaloriesBurned","Steps","Floors","Pace"]
    data=c._get_day_details(detailed,date)
    for datatype in detailed:
        dump_to_file(datatype, date, data[datatype])
    return True

if __name__ == '__main__':
    #import logging
    #logging.basicConfig(level=logging.DEBUG)
    client = fitbit.Client.login(options.email, options.password)

    sync_date = datetime.date.today()

    # Look for the most recent data on server
    while (datetime.date.today() - sync_date).days < 365:
        r = dump_day(client, sync_date)
        if r:
            break
        sync_date -= datetime.timedelta(days=1)
    print "Most recent fitbit data on server : ", sync_date

    if (datetime.date.today() - sync_date).days > 365:
        print "No data found for last year, exiting."
        sys.exit(1)

    # Sync of new days
    date=sync_date - datetime.timedelta(days=1)
    nEmptyDay = 0
    while not previously_dumped(date):
        print "Syncing ", date
        r = dump_day(client, date)
        date -= datetime.timedelta(days=1)
        if not r:
            nEmptyDay+=1
            if nEmptyDay>options.nEmptyDayMax:
                print "More than ",options.nEmptyDayMax, " days without steps, exiting."
                break
        else:
            nEmptyDay = 0

    # Always redump the last dumped day because we may have dumped it before the day was finished.
    print "Syncing ", date, " again (it was last sync, so probably before the day was finished)"
    dump_day(client, date)
    if options.continue_dumping_old:
        end_date=date
        date=min(end_date,sync_date)
        start_date = datetime.datetime.strptime(options.start_date,'%Y-%m-%d').date()
        while date > start_date:
	    if options.force or not previously_dumped(date):
	        r = dump_day(client, date)
                print "Syncing ", date, ", data : ",r 
            else:
                print "Already synced : ", date
            date -= datetime.timedelta(days=1) 
    print "Done."
