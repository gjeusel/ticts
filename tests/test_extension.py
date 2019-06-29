from datetime import timedelta

import pandas as pd

from ticts import TimeSeries


def test_to_dataframe(smallts):
    df = smallts.to_dataframe()
    assert isinstance(df, pd.DataFrame)


def test_sample_period(smallts: TimeSeries):
    sr = smallts.sample_period(sampling_period="3H", operation="min")
    assert all(sr == [0, 3, 6])

    sr = smallts.sample_period(sampling_period="3H", operation="max")
    assert all(sr == [2, 5, 8])

    sr = smallts.sample_period(sampling_period="3H", operation="mean")
    assert all(sr == [1, 4, 7])

    sr = smallts.sample_period(sampling_period="3H", end=smallts.upper_bound + timedelta(days=1), operation="mean")
    assert all(sr == [1.0, 4.0, 7.0, 9.0, 9.0, 9.0, 9.0, 9.0, 9.0, 9.0, 9.0])

    assert isinstance(sr, pd.Series)
