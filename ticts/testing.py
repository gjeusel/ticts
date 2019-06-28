from .timeseries import TimeSeries


def assert_ts_equal(ts1, ts2):
    for ts in [ts1, ts2]:
        if not isinstance(ts, TimeSeries):
            msg = "{} is not of type TimeSeries"
            raise TypeError(msg.format(type(ts)))
    assert ts1.equals(ts2)
