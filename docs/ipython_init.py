import logging
import pytz
import datetime
from pathlib import Path

try:
    import pandas as pd
    pd.options.display.max_rows = 10

    emptydf = pd.DataFrame()

    # Recent Dates aware:
    now = pd.Timestamp.now(tz="CET").replace(microsecond=0)
    end = pd.Timestamp(now, tz="CET") + pd.Timedelta(hours=4)
    start = end - pd.Timedelta(days=3)

    # DST
    dst_start = pd.Timestamp("2017-03-26T00:00:00", tz="CET")
    dst_end = pd.Timestamp("2017-03-26T04:00:00", tz="CET")

    # 2016
    start_2016 = pd.Timestamp("2016-01-01T00:00:00", tz="CET")
    end_2016 = pd.Timestamp("2017-01-01T00:00:00", tz="CET")

    # 2017
    start_2017 = pd.Timestamp("2017-01-01T00:00:00", tz="CET")
    end_2017 = pd.Timestamp("2017-01-01T00:00:00", tz="CET")

    # 2018
    start_2018 = pd.Timestamp("2018-01-01T00:00:00", tz="CET")
    end_2018 = pd.Timestamp("2018-01-01T00:00:00", tz="CET")

    # timedeltas aliases:
    onehour = pd.Timedelta(hours=1)
    tenhours = pd.Timedelta(hours=10)
    oneday = pd.Timedelta(days=1)
    oneweek = pd.Timedelta(days=7)
    onemonth = pd.Timedelta(days=31)
except Exception as e:
    print("Could not import pandas as pd: {}".format(e))
