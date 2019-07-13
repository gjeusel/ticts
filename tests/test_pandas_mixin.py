import pandas as pd
import pytest
from pandas.tseries.frequencies import to_offset

from ticts import TimeSeries, testing

from .conftest import CURRENT, HALFHOUR, ONEHOUR, ONEMIN


def test_to_dataframe(smallts):
    smallts.name = 'SuperTS'
    df = smallts.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert df.columns.to_list() == ['SuperTS']


def test_from_df_to_ticst(smallts):
    df = smallts.to_dataframe()
    returned = df.to_ticts()
    testing.assert_ts_equal(smallts, returned)


def test_from_series_to_ticst(smallts):
    serie = smallts.to_dataframe()['value']
    returned = serie.to_ticts()
    testing.assert_ts_equal(smallts, returned)


class TestTimeSeriesSample:
    def test_it_raises_when_both_freq_and_index_are_none(self, smallts):
        with pytest.raises(Exception) as err:
            smallts.sample()
        assert "Both are None" in str(err.value)

    def test_simple_sample_on_default(self, smallts):
        ts = smallts.sample(HALFHOUR)
        expected_dict = {
            **smallts.data,
            **{key + HALFHOUR: smallts[key]
               for key in smallts.index[:-1]}
        }
        expected_ts = TimeSeries(expected_dict, default=smallts.default)
        testing.assert_ts_equal(expected_ts, ts)

    def test_simple_by_passing_an_index(self, smallts):
        index = pd.date_range(
            start=smallts.lower_bound,
            end=smallts.upper_bound + 10 * ONEHOUR,
            freq='3H',
            closed='left')
        ts = smallts.sample(index=index)
        assert list(ts.index) == index.to_list()

    def test_simple_sample_with_start_being_string(self, smallts):
        start = '2019-01-01T09:00:00'
        ts = smallts.sample(HALFHOUR, start=start)
        expected_ts = TimeSeries({start: 9})
        testing.assert_ts_equal(expected_ts, ts)

    def test_sample_out_of_left_bound_with_no_default_permissive_shorten_interval(
            self, smallts):
        ts = smallts.sample(
            freq=HALFHOUR, start=CURRENT - ONEHOUR, end=CURRENT + ONEHOUR)
        expected_ts = TimeSeries({CURRENT: 0, CURRENT + HALFHOUR: 0})
        testing.assert_ts_equal(expected_ts, ts)

    def test_sample_on_empty_return_empty_df(self, emptyts):
        assert emptyts.sample(freq=ONEHOUR).empty

    def test_sample_with_start_out_of_left_bounds_with_default(
            self, smallts_withdefault):
        ts = smallts_withdefault.sample(freq=HALFHOUR, start=CURRENT - ONEHOUR)
        default = smallts_withdefault.default
        assert ts[CURRENT - ONEHOUR] == default
        assert ts[CURRENT - HALFHOUR] == default
        assert ts[CURRENT] == 0
        assert CURRENT + HALFHOUR in ts.index

    def test_sample_with_start_out_of_left_bounds(self, smallts):
        ts = smallts.sample(freq=HALFHOUR, start=CURRENT - ONEHOUR)
        CURRENT - ONEHOUR not in ts.index
        CURRENT - HALFHOUR not in ts.index
        assert ts[CURRENT] == 0
        assert CURRENT + HALFHOUR in ts.index

    @pytest.mark.parametrize('freq', [
        ONEMIN,
        10 * ONEMIN,
        '10Min',
        pd.Timedelta(seconds=10),
        ONEHOUR,
        '1H',
    ])
    def test_sample_on_freq_with_end_and_start_in_bound(self, otherts, freq):
        start = CURRENT + 2 * ONEHOUR + HALFHOUR
        end = CURRENT + 3 * ONEHOUR + HALFHOUR
        ts = otherts.sample(freq=freq, start=start, end=end)
        freq = pd.Timedelta(freq)
        expected = [start + i * freq for i in range(int((end - start) / freq))]
        assert list(ts.index) == expected

    @pytest.mark.parametrize('freq', ['MS', 'M', 'B'])
    def test_sample_on_non_fixed_frequency(self, smallts, freq):
        ts = smallts.sample(freq)
        for start, end in ts.iterintervals():
            to_offset(end - start) == to_offset(freq)

    def test_sample_on_non_fixed_frequency_with_values(self, smallts):
        freq = to_offset('MS')
        ts = smallts.sample(freq)
        expected_index = [smallts.lower_bound, smallts.lower_bound + freq]
        list(ts.index) == expected_index
        expected_values = [
            smallts[smallts.lower_bound], smallts[smallts.lower_bound + freq]
        ]
        list(ts.values()) == expected_values
