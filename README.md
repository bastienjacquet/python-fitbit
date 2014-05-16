# Overview

This client provides a simple way to reclaim more of your data from www.fitbit.com than is possible with the official API.

# Example

    import fitbit

    client = fitbit.Client.login(user, password)

    # example data
    data = client.intraday_steps(datetime.date(2010, 2, 21))

    # data will be a list of tuples. example:
    # [
    #   (datetime.datetime(2010, 2, 21, 0, 0), 0),
    #   (datetime.datetime(2010, 2, 21, 0, 5), 40),
    #   ....
    #   (datetime.datetime(2010, 2, 21, 23, 55), 64),
    # ]
    
    # The timestamp is the beginning of the 5 minute range the value is for
    
    # Other intraday calls:
    data = client.intraday_calories_burned(datetime.date(2010, 2, 21))
    data = client.intraday_active_score(datetime.date(2010, 2, 21))
    
    # Sleep data is a little different:
    data = client.intraday_sleep(datetime.date(2010, 2, 21))
    
    # data will be a similar list of tuples, but spaced one minute apart
    # [
    #   (datetime.datetime(2010, 2, 20, 23, 59), 2),
    #   (datetime.datetime(2010, 2, 21, 0, 0), 1),
    #   (datetime.datetime(2010, 2, 21, 0, 1), 1),
    #   ....
    #   (datetime.datetime(2010, 2, 21, 8, 34), 1),
    # ]
    
    # The different values for sleep are:
    #   0: no sleep data
    #   1: asleep
    #   2: awake
    #   3: very awake

    # Activity log
    logs=client.activity_logs(datetime.date(2014, 5, 16))  

    # data will be a list of (id,timestamp,name,steps,distance (km),duration (s),calories) tuples
    # [
    #   (12345678, datetime.datetime(2014, 5, 16, 10, 16, tzinfo=tzlocal()), u'Activity record', 74, 0.0654321, datetime.timedelta(0, 660), 22),
    #   (12345679, datetime.datetime(2014, 5, 16, 11, 10, tzinfo=tzlocal()), u'Activity record', 100, 0.0876543, datetime.timedelta(0, 780), 30),
    #   ...
    # ]

    # Activity log data
    for log in logs:
        activity_step_data=client.activity_log_data_steps(datetime.date(2014, 5, 16),log[0])

        # data will be a list of (timestamp,steps) tuples at one minute intervals
        # [
        #   (datetime.datetime(2014, 5, 16, 10, 16), 120), 
        #   (datetime.datetime(2014, 5, 16, 10, 17), 122),
        #   ...
        # ]

        # other activity log data calls with similar tuple results
        activity_calory_data=client.activity_log_data_calories(datetime.date(2014, 5, 16),log[0])
        activity_floor_data=client.activity_log_data_floors(datetime.date(2014, 5, 16),log[0])
        activity_pace_data=client.activity_log_data_pace(datetime.date(2014, 5, 16),log[0])

        # or get all of them in one go:
        client.activity_log_data_all(datetime.date(2014, 5, 16),log[0])

        # data will be a list of (timestamp,calories,steps,floors,pace) tuples at one minute intervals
        # [
        #   (datetime.datetime(2014, 5, 16, 10, 25), 4, 53, 0, 35), 
        #   (datetime.datetime(2014, 5, 16, 10, 26), 3, 5, 0, 378),
        #   ...
        # ]

There is also an example dump script provided: `examples/dump.py`.  This script can be set up as a cron job to dump data nightly.
