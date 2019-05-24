from copy import copy, deepcopy
from unittest import mock

import pytest

from ticts import TimeSeries

from .conftest import CURRENT, ONEHOUR, ONEMIN


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


class TestTimeSeriesGetitem:
    @mock.patch("ticts.TimeSeries._get_previous")
    def test_get_default_on_previous(self, _get_previous, smallts):
        smallts[CURRENT]
        assert _get_previous.call_count == 1

    def test_get_on_previous(self, smallts):
        assert smallts[CURRENT + ONEMIN] == 0

    def test_get_on_previous_out_of_left_bound(self, smallts):
        assert smallts[CURRENT - ONEMIN] == 0

    def test_get_on_previous_out_of_right_bound(self, smallts):
        assert smallts[CURRENT + 10 * ONEHOUR] == 9

    def test_get_on_previous_on_emtpy_raises_keyerror(self, emptyts):
        with pytest.raises(KeyError):
            assert emptyts[CURRENT]

    def test_get_on_previous_on_emtpy_with_default_return_default(
            self, emptyts_withdefault):
        assert emptyts_withdefault[CURRENT] == emptyts_withdefault.default

    def test_get_linear_interpolate_raises(self, smallts):
        with pytest.raises(NotImplementedError):
            smallts[CURRENT, "linear"]

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


class TestTimeSeriesCopy:
    def test_copy(self, smallts):
        copied = copy(smallts)
        assert copied == smallts

    def test_deepcopy(self, smallts):
        deepcopied = deepcopy(smallts)
        assert deepcopied == smallts


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


def test_timeseries_set(smallts):
    smallts[CURRENT] = 1000
    assert smallts[CURRENT] == 1000


def test_timeseries_compact(smallts):
    smallts[CURRENT + ONEMIN] = 0
    assert (CURRENT + ONEMIN) not in smallts.compact().keys()
