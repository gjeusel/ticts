import pandas as pd


def timestamp_converter(ts):
    ts = pd.Timestamp(ts)
    if not ts.tz:
        ts = ts.tz_localize('UTC')
    return ts


MINTS = pd.Timestamp.min.tz_localize('UTC')
MAXTS = pd.Timestamp.max.tz_localize('UTC')
