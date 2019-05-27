import arrow

try:
    PANDAS_IS_INSTALLED = True
    import pandas as pd
except ImportError:
    PANDAS_IS_INSTALLED = False


def timestamp_converter(ts):
    if PANDAS_IS_INSTALLED:
        if isinstance(ts, arrow.Arrow):
            ts = ts.isoformat()
        ts = pd.Timestamp(ts)
        if not ts.tz:
            ts = ts.tz_localize('UTC')
        return ts
    else:
        return arrow.get(ts)


def to_dataframe(self):
    return pd.DataFrame(data={'value': self.values()}, index=self.keys())
