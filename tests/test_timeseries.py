from copy import copy, deepcopy
from datetime import timedelta
from unittest import mock

import pytest

from ticts import TimeSeries

from .conftest import CURRENT, HALFHOUR, ONEHOUR, ONEMIN


class TestTimeSeriesInit:
    def test_with_dict(self, smalldict):
        ts = TimeSeries(smalldict)
        assert ts[CURRENT + ONEHOUR] == 1

    def test_with_data_as_tuple(self):
        mytuple = ((CURRENT, 0), (CURRENT + ONEHOUR, 1))
        ts = TimeSeries(mytuple)
        assert ts[CURRENT] == 0
        assert ts[CURRENT + ONEHOUR] == 1
        assert len(ts) == 2


class TestTimeSeriesSetItem:
    def test_simple_setitem(self, smallts):
        smallts[CURRENT] = 1000
        assert smallts[CURRENT] == 1000

    def test_consecutive_setitem(self, smallts):
        smallts[CURRENT] = 1000
        first_time = deepcopy(smallts)
        smallts[CURRENT] = 1000
        assert first_time == smallts

    @mock.patch("ticts.TimeSeries.set_interval")
    def test_setitem_on_slice_calls_set_interval(self, set_interval, smallts):
        smallts[CURRENT:CURRENT + 2 * ONEHOUR] = 1000
        assert set_interval.call_count == 1


class TestTimeSeriesCopy:
    def test_copy(self, smallts):
        copied = copy(smallts)
        assert copied == smallts

    def test_deepcopy(self, smallts):
        deepcopied = deepcopy(smallts)
        assert deepcopied == smallts


def test_timeseries_compact(smallts):
    smallts[CURRENT + ONEMIN] = 0
    assert (CURRENT + ONEMIN) not in smallts.compact().keys()


class TestTimeSeriesGetitem:
    available_interpolate = ['previous', 'linear']

    # tests on corner cases

    def test_getitem_out_of_left_bound_with_no_default_raises(self, smallts):
        with pytest.raises(KeyError) as err:
            smallts[CURRENT - ONEMIN]

        assert 'default attribute is not set' in str(err)

    @pytest.mark.parametrize('interpolate', available_interpolate)
    def test_getitem_out_of_left_bound_with_default_return_default(
            self, smallts_withdefault, interpolate):
        value = smallts_withdefault[CURRENT - ONEMIN, interpolate]
        assert value == smallts_withdefault.default

    @pytest.mark.parametrize('interpolate', available_interpolate)
    def test_getitem_on_empty_when_no_default_raises(self, emptyts,
                                                     interpolate):
        with pytest.raises(KeyError) as err:
            emptyts[CURRENT - ONEMIN, interpolate]

        assert str(
            "default attribute is not set and timeseries is empty") in str(err)

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

    # test on 'slice'

    def test_get_on_slice_exclude_upper_bound_include_lower_bound(
            self, smallts):
        data = {
            CURRENT: 0,
            CURRENT + ONEHOUR: 1,
        }
        expected_ts = TimeSeries(
            data,
            default=smallts.default,
        )
        assert smallts[CURRENT:CURRENT + 2 * ONEHOUR] == expected_ts


class TestTimeSeriesSetInterval:
    def test_single_set_interval_end_on_last_key(self, smallts):
        smallts.set_interval(CURRENT + ONEHOUR, CURRENT + 9 * ONEHOUR, 1000)
        expected_keys = [CURRENT, CURRENT + ONEHOUR, CURRENT + 9 * ONEHOUR]
        assert list(smallts.keys()) == expected_keys
        assert smallts[CURRENT + ONEHOUR] == 1000

    def test_single_set_interval_start_on_first_key(self, smallts):
        smallts.set_interval(CURRENT, CURRENT + 9 * ONEHOUR, 1000)
        expected_keys = [CURRENT, CURRENT + 9 * ONEHOUR]
        assert list(smallts.keys()) == expected_keys
        assert smallts[CURRENT] == 1000

    def test_single_set_interval_end_over_last_key(self, smallts):
        last_val = smallts[CURRENT + 9 * ONEHOUR]
        smallts.set_interval(CURRENT + ONEHOUR, CURRENT + 10 * ONEHOUR, 1000)
        expected_keys = [CURRENT, CURRENT + ONEHOUR, CURRENT + 10 * ONEHOUR]
        assert list(smallts.keys()) == expected_keys
        assert smallts[CURRENT + 10 * ONEHOUR] == last_val

    def test_single_set_interval_start_before_first_key(self, smallts):
        smallts.set_interval(CURRENT - ONEHOUR, CURRENT + 9 * ONEHOUR, 1000)
        expected_keys = [CURRENT - ONEHOUR, CURRENT + 9 * ONEHOUR]
        assert list(smallts.keys()) == expected_keys
        assert smallts[CURRENT - 1 * ONEHOUR] == 1000

    def test_single_set_interval_on_bounds_not_being_keys(self, smallts):
        smallts.set_interval(CURRENT + ONEMIN, CURRENT + 9 * ONEHOUR, 1000)
        expected_keys = [CURRENT, CURRENT + ONEMIN, CURRENT + 9 * ONEHOUR]
        assert list(smallts.keys()) == expected_keys
        assert smallts[CURRENT + ONEMIN] == 1000

    def test_set_interval_on_empty(self, emptyts):
        emptyts.set_interval(CURRENT, CURRENT + ONEHOUR, 1)
        assert emptyts[CURRENT] == 1
        len(emptyts.keys()) == 1

    def test_set_interval_on_empty_with_default(self, emptyts_withdefault):
        emptyts_withdefault.set_interval(CURRENT, CURRENT + ONEHOUR, 1)
        assert emptyts_withdefault[CURRENT] == 1
        assert emptyts_withdefault[CURRENT +
                                   ONEHOUR] == emptyts_withdefault.default
        len(emptyts_withdefault.keys()) == 2

    def test_same_consecutive_set_interval(self, smallts):
        smallts.set_interval(CURRENT, CURRENT + 9 * ONEHOUR, 1000)
        first_time = deepcopy(smallts)
        smallts.set_interval(CURRENT, CURRENT + 9 * ONEHOUR, 1000)
        assert first_time == smallts


class TestTimeSeriesOperators:
    def test_simple_add(self, smallts, smalldict):
        ts = smallts + smallts
        newdct = {key: value + value for key, value in smalldict.items()}
        assert ts == TimeSeries(newdct)

    def test_simple_add_one_float(self, smallts, smalldict):
        ts = smallts + 1000
        assert list(ts.values()) == list(range(1000, 1010))

    def test_add_with_keys_differences(self, smallts_withdefault,
                                       otherts_withdefault):
        ts = smallts_withdefault + otherts_withdefault
        assert ts[CURRENT + 1 * ONEHOUR] == 1 + otherts_withdefault.default
        assert ts[CURRENT + 2 * ONEHOUR] == 2 + 1000
        assert ts[CURRENT + 2 * ONEHOUR + 30 * ONEMIN] == 2 + 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 3 + 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 4 + 3000

    def test_simple_sub(self, smallts):
        ts = smallts - smallts
        assert all([val == 0 for val in ts.values()])

    def test_simple_sub_one_float(self, smallts):
        ts = smallts - 1
        assert list(ts.values()) == list(range(-1, 9))

    def test_sub_with_keys_differences(self, smallts_withdefault,
                                       otherts_withdefault):
        ts = smallts_withdefault - otherts_withdefault
        assert ts[CURRENT + 1 * ONEHOUR] == 1 - 900
        assert ts[CURRENT + 2 * ONEHOUR] == 2 - 1000
        assert ts[CURRENT + 2 * ONEHOUR + 30 * ONEMIN] == 2 - 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 3 - 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 4 - 3000

    def test_floor_on_float(self, smallts):
        ts = smallts.floor(2)
        assert all([value <= 2 for value in ts.values()])

    def test_floor_on_ts(self, smallts_withdefault, otherts_withdefault):
        ts = smallts_withdefault.floor(otherts_withdefault)
        assert ts[CURRENT + 1 * ONEHOUR] == 1
        assert ts[CURRENT + 2 * ONEHOUR] == 2
        assert ts[CURRENT + 2 * ONEHOUR + 30 * ONEMIN] == 2
        assert ts[CURRENT + 3 * ONEHOUR] == 3
        assert ts[CURRENT + 4 * ONEHOUR] == 4

    def test_ceil_on_float(self, smallts):
        ts = smallts.ceil(7)
        assert all([value >= 7 for value in ts.values()])

    def test_ceil_on_ts(self, smallts_withdefault, otherts_withdefault):
        ts = smallts_withdefault.ceil(otherts_withdefault)
        assert ts[CURRENT + ONEHOUR] == 900
        assert ts[CURRENT + 2 * ONEHOUR] == 1000
        assert ts[CURRENT + 2 * ONEHOUR + 30 * ONEMIN] == 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 3000

    def test_ceil_on_ts_check_changing_default(self, smallts_withdefault,
                                               otherts_withdefault):
        otherts_withdefault.default = -10
        ts = smallts_withdefault.ceil(otherts_withdefault)

        assert ts[CURRENT + ONEHOUR] == 1
        assert ts[CURRENT + 2 * ONEHOUR] == 1000
        assert ts[CURRENT + 2 * ONEHOUR + 30 * ONEMIN] == 2000
        assert ts[CURRENT + 3 * ONEHOUR] == 2000
        assert ts[CURRENT + 4 * ONEHOUR] == 3000


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
        assert ts == expected_ts

    def test_sample_raises_when_no_default_and_start_lower_than_all_keys(
            self, smallts):
        with pytest.raises(KeyError) as err:
            smallts.sample(freq=HALFHOUR, start=CURRENT - ONEHOUR)

        assert "default attribute is not set, can't deduce value" in str(err)

    def test_sample_with_start_lower_than_all_keys(self, smallts_withdefault):
        ts = smallts_withdefault.sample(freq=HALFHOUR, start=CURRENT - ONEHOUR)
        default = smallts_withdefault.default
        assert ts[CURRENT - ONEHOUR] == default
        assert ts[CURRENT - HALFHOUR] == default
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
