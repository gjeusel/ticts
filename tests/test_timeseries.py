from copy import copy, deepcopy
from datetime import datetime, timedelta
from unittest import mock

import pandas as pd
import pytest

from ticts import TimeSeries, testing
from ticts.utils import MAXTS, MINTS, timestamp_converter

from .conftest import CURRENT, HALFHOUR, ONEHOUR, ONEMIN


class TestTimeSeriesInit:
    def test_with_dict(self, smalldict):
        ts = TimeSeries(smalldict, default=10)
        assert ts[CURRENT + ONEHOUR] == 1
        assert ts.default == 10

    def test_with_dict_keys_being_strings(self):
        dct = {
            '2019-01-01': 1,
            '2019-02-01': 2,
            timestamp_converter('2019-03-01'): 3,
        }
        ts = TimeSeries(dct, default=10)
        expected = {
            timestamp_converter(key): value
            for key, value in dct.items()
        }
        assert ts.items() == expected.items()
        assert ts.default == 10

    def test_with_data_as_tuple(self):
        mytuple = (
            (CURRENT, 0),
            ('2019-02-01', 1),
        )
        ts = TimeSeries(mytuple, default=10)
        assert ts[CURRENT] == 0
        assert ts['2019-02-01'] == 1
        assert len(ts) == 2
        assert ts.default == 10

    def test_with_data_as_pandas_series(self, smalldict):
        serie = pd.Series(data=smalldict, name='SomeName')
        ts = TimeSeries(serie)
        assert ts.name == 'SomeName'
        assert ts[CURRENT] == 0
        assert len(ts) == len(serie)

    def test_with_data_as_dataframe(self, smalldict):
        df = pd.DataFrame(
            data={'SomeName': list(smalldict.values())},
            index=smalldict.keys())
        ts = TimeSeries(df, default=10)
        assert ts[CURRENT] == 0
        assert ts.name == 'SomeName'
        assert len(ts) == df.shape[0]
        assert ts.default == 10

    def test_with_data_as_dataframe_raises_when_several_columns(self):
        df = pd.DataFrame(columns=['Too', 'Many', 'Columns'])
        with pytest.raises(Exception) as err:
            TimeSeries(df)

        expected = "Can't convert a DataFrame with several columns"
        assert expected in str(err.value)


class TestTimeSeriesSetItem:
    def test_simple_setitem(self, smallts):
        smallts[CURRENT] = 1000
        assert smallts[CURRENT] == 1000

    def test_consecutive_setitem(self, smallts):
        smallts[CURRENT] = 1000
        first_time = deepcopy(smallts)
        smallts[CURRENT] = 1000
        testing.assert_ts_equal(first_time, smallts)

    @mock.patch("ticts.TimeSeries.set_interval")
    def test_setitem_on_slice_calls_set_interval(self, set_interval, smallts):
        smallts[CURRENT:CURRENT + 2 * ONEHOUR] = 1000
        assert set_interval.call_count == 1


class TestTimeSeriesCopy:
    def test_copy(self, smallts):
        copied = copy(smallts)
        testing.assert_ts_equal(copied, smallts)

    def test_copy_with_default(self, smallts_withdefault):
        copied = copy(smallts_withdefault)
        testing.assert_ts_equal(copied, smallts_withdefault)

    def test_deepcopy(self, smallts):
        deepcopied = deepcopy(smallts)
        testing.assert_ts_equal(deepcopied, smallts)

    def test_deepcopy_with_default(self, smallts_withdefault):
        deepcopied = deepcopy(smallts_withdefault)
        testing.assert_ts_equal(deepcopied, smallts_withdefault)


class TestTimeSeriesRepr:
    def test_repr_on_otherts(self, otherts):
        assert repr(otherts).count('\n') == 3

    def test_repr_on_large(self):
        dct = dict()
        for i in range(100):
            dct[CURRENT + i * ONEHOUR] = i
        ts = TimeSeries(dct)
        assert repr(ts).count('\n') == 11

    def test_repr_with_default_and_name(self, smallts_withdefault):
        smallts_withdefault.name = 'SuperCool'
        assert 'default=' in repr(smallts_withdefault)
        assert 'name=' in repr(smallts_withdefault)


class TestTimeSeriesDefault:
    @pytest.mark.parametrize('default', [None, 0, False])
    def test_it_has_default(self, default):
        ts = TimeSeries(default=default)
        assert ts._has_default

    def test_it_has_no_default(self):
        ts = TimeSeries()
        assert not ts._has_default


class TestTimeSeriesEqual:
    def test_equals(self, smallts_withdefault):
        assert smallts_withdefault.equals(smallts_withdefault) is True

    def test_not_equals(self, smallts, otherts):
        assert smallts.equals(otherts) is False

    def test_not_equals_due_to_default(self, smallts, smallts_withdefault):
        assert smallts_withdefault.equals(smallts) is False

    def test_equals_without_default(self, smallts, smallts_withdefault):
        assert smallts_withdefault.equals(smallts, check_default=False) is True


class TestTimeSeriesBoundProperties:
    def test_lower_bound(self, smallts):
        assert smallts.lower_bound == smallts.keys()[0]

    def test_upper_bound(self, smallts):
        assert smallts.upper_bound == smallts.keys()[-1]

    def test_lower_bound_on_empty(self, emptyts):
        assert emptyts.lower_bound == MINTS

    def test_upper_bound_on_empty(self, emptyts):
        assert emptyts.upper_bound == MAXTS


def test_timeseries_compact(smallts):
    smallts[CURRENT + ONEMIN] = 0
    assert (CURRENT + ONEMIN) not in smallts.compact().keys()


class TestTimeSeriesGetitem:
    available_interpolate = ['previous', 'linear']

    # tests on corner cases

    def test_get_item_out_of_left_bound_with_default_zero(self):
        mytuple = ((CURRENT, 0), (CURRENT + ONEHOUR, 1))
        ts = TimeSeries(mytuple, default=0)
        assert ts[CURRENT + ONEHOUR] == 1
        assert ts[CURRENT - ONEHOUR] == 0

    def test_getitem_out_of_left_bound_with_no_default_and_permissive_return_None(
            self, smallts):
        assert smallts[CURRENT - ONEMIN] is None

    def test_getitem_out_of_left_bound_with_no_default_and_not_permissive_raises(
            self, smallts):
        smallts.permissive = False
        with pytest.raises(KeyError) as err:
            smallts[CURRENT - ONEMIN]
        assert 'default attribute is not set' in str(err.value)

    def test_getitem_using_str(self, smallts):
        smallts['2019-01-01'] == 0

    @pytest.mark.parametrize('interpolate', available_interpolate)
    def test_getitem_out_of_left_bound_with_default_return_default(
            self, smallts_withdefault, interpolate):
        value = smallts_withdefault[CURRENT - ONEMIN, interpolate]
        assert value == smallts_withdefault.default

    @pytest.mark.parametrize('interpolate', available_interpolate)
    def test_getitem_on_empty_when_no_default_not_permissive_raises(
            self, emptyts, interpolate):
        emptyts.permissive = False
        with pytest.raises(KeyError) as err:
            emptyts[CURRENT - ONEMIN, interpolate]

        expected = "default attribute is not set and timeseries is empty"
        assert expected in str(err.value)

    @pytest.mark.parametrize('interpolate', available_interpolate)
    def test_getitem_on_empty_when_no_default_return_None(
            self, emptyts, interpolate):
        emptyts[CURRENT - ONEMIN, interpolate] is None

    # tests on '_get_previous'

    @mock.patch("ticts.TimeSeries._get_previous")
    def test_get_on_previous_is_default_interpolate(self, _get_previous,
                                                    smallts):
        smallts[CURRENT + ONEMIN]
        assert _get_previous.call_count == 1

    def test_get_on_previous(self, smallts):
        assert smallts[CURRENT + ONEMIN] == 0

    def test_get_on_previous_out_of_right_bound(self, smallts):
        assert smallts[CURRENT + 10 * ONEHOUR] == 9

    def test_get_on_previous_out_of_left_bound_no_default(self, smallts):
        assert smallts[CURRENT - ONEHOUR] is None

    def test_get_on_previous_out_of_left_bound_with_default(
            self, smallts_withdefault):
        assert smallts_withdefault[CURRENT -
                                   ONEHOUR] == smallts_withdefault.default

    # tests on '_get_linear_interpolate'

    @pytest.mark.parametrize('time_idx, expected', [
        (CURRENT + HALFHOUR, 0.5),
        (CURRENT + ONEHOUR + HALFHOUR, 1.5),
        (CURRENT + 10 * ONEMIN, 0 + (1 - 0) * (10 * ONEMIN / ONEHOUR)),
    ])
    def test_get_linear_interpolate(self, smallts, time_idx, expected):
        assert smallts[time_idx, 'linear'] == expected

    def test_get_linear_interpolate_out_of_right_bound(self, smallts):
        assert smallts[CURRENT + 10 * ONEHOUR, 'linear'] == 9

    def test_get_linear_interpolate_out_of_left_bound_no_default(
            self, smallts):
        assert smallts[CURRENT - ONEHOUR, 'linear'] is None

    def test_get_linear_interpolate_out_of_left_bound_with_default(
            self, smallts_withdefault):
        assert smallts_withdefault[CURRENT - ONEHOUR,
                                   'linear'] == smallts_withdefault.default

    # test on 'slice'

    def test_get_on_slice_exclude_upper_bound_include_lower_bound(
            self, smallts):
        start = CURRENT
        end = CURRENT + 1 * ONEHOUR
        sliced_ts = smallts[start:end + ONEHOUR]

        data = {start: 0, end: 1}
        expected_ts = TimeSeries(data, default=smallts.default)
        testing.assert_ts_equal(sliced_ts, expected_ts)

    def test_get_on_slice_add_back_previous_value_if_start_not_in_keys(
            self, smallts):
        start = CURRENT + HALFHOUR
        end = CURRENT + ONEHOUR
        sliced_ts = smallts[start:end + ONEHOUR]

        data = {start: 0, end: 1}
        expected_ts = TimeSeries(data, default=smallts.default)
        testing.assert_ts_equal(sliced_ts, expected_ts)

    def test_get_on_slice_entirely_out_of_bounds_on_left_side(self, smallts):
        assert smallts[CURRENT - 2 * ONEHOUR:CURRENT - 1 * ONEHOUR].empty

    def test_get_on_slice_out_of_bounds_left_side(self, smallts):
        start = CURRENT - 2 * ONEHOUR
        end = CURRENT
        data = {CURRENT: 0}
        sliced_ts = smallts[start:end + 1 * ONEHOUR]
        expected_ts = TimeSeries(data, default=smallts.default)
        testing.assert_ts_equal(sliced_ts, expected_ts)

    def test_get_on_slice_entirely_out_of_bounds_on_right_side(self, smallts):
        start = CURRENT + 10 * ONEHOUR
        end = CURRENT + 12 * ONEHOUR
        sliced_ts = smallts[start:end]
        expected_ts = TimeSeries({start: smallts[start]})
        testing.assert_ts_equal(sliced_ts, expected_ts)

    def test_get_on_slice_out_of_bounds_on_right_side(self, smallts):
        sliced_ts = smallts[CURRENT + 9 * ONEHOUR:CURRENT + 12 * ONEHOUR]
        expected_dct = {CURRENT + 9 * ONEHOUR: 9}
        expected_ts = TimeSeries(expected_dct, default=smallts.default)
        testing.assert_ts_equal(sliced_ts, expected_ts)


class TestTimeSeriesSetInterval:
    def test_set_interval_when_no_default_raises(self, smallts):
        with pytest.raises(NotImplementedError):
            smallts.set_interval(CURRENT, CURRENT + ONEHOUR, 1000)

    def test_single_set_interval_end_on_last_key(self, smallts_withdefault):
        smallts_withdefault.set_interval(CURRENT + ONEHOUR,
                                         CURRENT + 9 * ONEHOUR, 1000)
        expected_keys = [CURRENT, CURRENT + ONEHOUR, CURRENT + 9 * ONEHOUR]
        assert list(smallts_withdefault.keys()) == expected_keys
        assert smallts_withdefault[CURRENT + ONEHOUR] == 1000
        assert smallts_withdefault[CURRENT + 9 * ONEHOUR] == 9.

    def test_single_set_interval_start_on_first_key(self, smallts_withdefault):
        smallts_withdefault.set_interval(CURRENT, CURRENT + 9 * ONEHOUR, 1000)
        expected_keys = [CURRENT, CURRENT + 9 * ONEHOUR]
        assert list(smallts_withdefault.keys()) == expected_keys
        assert smallts_withdefault[CURRENT] == 1000
        assert smallts_withdefault[CURRENT + 9 * ONEHOUR] == 9.

    @pytest.mark.parametrize('start, end', [
        (CURRENT + ONEHOUR, CURRENT + 10 * ONEHOUR),
        (CURRENT + 4 * ONEHOUR, CURRENT + 11 * ONEHOUR),
    ])
    def test_single_set_interval_end_over_last_key_sets_to_last_value(
            self, smallts_withdefault, start, end):
        last_key = smallts_withdefault.keys()[-1]
        last_val = smallts_withdefault[last_key]

        smallts_withdefault.set_interval(start, end, 1000)
        keys_before_start = []
        for key in smallts_withdefault.keys():
            if key < start:
                keys_before_start.append(key)

        expected_keys = [*keys_before_start, start, end]
        assert list(smallts_withdefault.keys()) == expected_keys
        assert smallts_withdefault[end] == last_val

    def test_single_set_interval_when_start_higher_than_upper_bound(
            self, smallts_withdefault):
        start = CURRENT + 11 * ONEHOUR
        end = CURRENT + 13 * ONEHOUR
        smallts_withdefault.set_interval(start, end, 1000)

        assert CURRENT + 10 * ONEHOUR not in smallts_withdefault.keys()
        assert smallts_withdefault[CURRENT + 10 * ONEHOUR] == 9

        assert smallts_withdefault[start] == 1000
        assert smallts_withdefault[end] == 9

    def test_single_set_interval_start_before_first_key(
            self, smallts_withdefault):
        smallts_withdefault.set_interval(CURRENT - ONEHOUR,
                                         CURRENT + 9 * ONEHOUR, 1000)
        expected_keys = [CURRENT - ONEHOUR, CURRENT + 9 * ONEHOUR]
        assert list(smallts_withdefault.keys()) == expected_keys
        assert smallts_withdefault[CURRENT - 1 * ONEHOUR] == 1000

    def test_single_set_interval_on_bounds_not_being_keys(
            self, smallts_withdefault):
        smallts_withdefault.set_interval(CURRENT + ONEMIN,
                                         CURRENT + 9 * ONEHOUR, 1000)
        expected_keys = [CURRENT, CURRENT + ONEMIN, CURRENT + 9 * ONEHOUR]
        assert list(smallts_withdefault.keys()) == expected_keys
        assert smallts_withdefault[CURRENT + ONEMIN] == 1000

    def test_set_interval_on_empty(self, emptyts):
        emptyts.default = 10
        emptyts.set_interval(CURRENT, CURRENT + ONEHOUR, 1)
        assert emptyts[CURRENT] == 1
        assert emptyts[CURRENT + ONEHOUR] == 10
        assert len(emptyts.keys()) == 2

    def test_set_interval_on_empty_with_default(self, emptyts_withdefault):
        emptyts_withdefault.set_interval(CURRENT, CURRENT + ONEHOUR, 1)
        assert emptyts_withdefault[CURRENT] == 1
        assert emptyts_withdefault[CURRENT +
                                   ONEHOUR] == emptyts_withdefault.default
        len(emptyts_withdefault.keys()) == 2

    @pytest.mark.parametrize('start, end', (
        (CURRENT, CURRENT + 9 * ONEHOUR),
        (CURRENT + 5 * ONEHOUR, CURRENT + 12 * ONEHOUR),
        (datetime(2019, 1, 1) + 5 * ONEHOUR,
         datetime(2019, 1, 1) + 12 * ONEHOUR),
        ('2019-01-01T05:00:00', '2019-01-01T12:00:00+02:00'),
    ))
    def test_same_consecutive_set_interval(self, smallts_withdefault, start,
                                           end):
        smallts_withdefault.set_interval(start, end, 1000)
        first_time = deepcopy(smallts_withdefault)

        for _ in range(10):
            smallts_withdefault.set_interval(start, end, 1000)

        testing.assert_ts_equal(first_time, smallts_withdefault)

    def test_consecutive_set_interval_on_empty_with_default(self, emptyts):
        emptyts.default = 10
        emptyts.set_interval(CURRENT, CURRENT + 2 * ONEHOUR, 10)
        emptyts.set_interval(CURRENT, CURRENT + ONEHOUR, 0)
        emptyts.set_interval(CURRENT + ONEHOUR, CURRENT + 2 * ONEHOUR, 1)
        emptyts.set_interval(CURRENT, CURRENT + 2 * ONEHOUR, 3)
        assert emptyts[CURRENT] == 3
        assert emptyts[CURRENT + 2 * ONEHOUR] == 10
        assert list(emptyts.keys()) == [CURRENT, CURRENT + 2 * ONEHOUR]

    def test_set_interval_when_no_keys_to_delete_with_default(self, emptyts):
        emptyts.default = 1000
        emptyts.set_interval(CURRENT, CURRENT + 1 * ONEHOUR, 0)
        emptyts.set_interval(CURRENT + 3 * ONEHOUR, CURRENT + 4 * ONEHOUR, 3)
        emptyts.set_interval(CURRENT + 1 * ONEHOUR + HALFHOUR,
                             CURRENT + 3 * ONEHOUR, 10)

        expected_dct = {
            CURRENT: 0,
            CURRENT + 1 * ONEHOUR: 1000.,
            CURRENT + 1 * ONEHOUR + HALFHOUR: 10,
            CURRENT + 3 * ONEHOUR: 3,
            CURRENT + 4 * ONEHOUR: 1000
        }
        assert list(emptyts.keys()) == list(expected_dct.keys())

        for key in expected_dct:
            assert emptyts[key] == expected_dct[key]


class TestTimeSeriesSample:
    def test_simple_sample_on_default(self, smallts):
        ts = smallts.sample(HALFHOUR)
        expected_dict = {
            **smallts,
            **{
                key + HALFHOUR: smallts[key]
                for key in list(smallts.keys())[:-1]
            }
        }
        expected_ts = TimeSeries(expected_dict, default=smallts.default)
        testing.assert_ts_equal(expected_ts, ts)

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
        assert CURRENT + HALFHOUR in ts.keys()

    def test_sample_with_start_out_of_left_bounds(self, smallts):
        ts = smallts.sample(freq=HALFHOUR, start=CURRENT - ONEHOUR)
        CURRENT - ONEHOUR not in ts.keys()
        CURRENT - HALFHOUR not in ts.keys()
        assert ts[CURRENT] == 0
        assert CURRENT + HALFHOUR in ts.keys()

    @pytest.mark.parametrize(
        'freq', [ONEMIN, 10 * ONEMIN,
                 timedelta(seconds=10), ONEHOUR])
    def test_sample_on_freq_with_end_and_start_in_bound(self, otherts, freq):
        start = CURRENT + 2 * ONEHOUR + HALFHOUR
        end = CURRENT + 3 * ONEHOUR + HALFHOUR
        ts = otherts.sample(freq=freq, start=start, end=end)
        assert list(ts.keys()) == [
            start + i * freq for i in range(int((end - start) / freq))
        ]


class TestIterIntervals:
    def test_simple_iterintervals(self, smallts):
        iterator = smallts.iterintervals()
        result = [(start, end) for start, end in iterator]
        expected = [(CURRENT + i * ONEHOUR, CURRENT + (i + 1) * ONEHOUR)
                    for i in range(9)]
        assert sorted(result) == sorted(expected)

    def test_iterintervals_with_end(self, smallts):
        end = CURRENT + 3 * ONEHOUR + HALFHOUR
        iterator = smallts.iterintervals(end)
        result = [(start, end) for start, end in iterator]
        expected = [(CURRENT + i * ONEHOUR, CURRENT + (i + 1) * ONEHOUR)
                    for i in range(3)]
        expected.append((CURRENT + 3 * ONEHOUR, end))
        assert sorted(result) == sorted(expected)
